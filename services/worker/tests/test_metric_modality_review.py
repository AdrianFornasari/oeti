"""Constructed controls and immutability tests; no predictions or network."""
from copy import deepcopy
import json
import unittest

from onehealth_worker.evaluation.metric_modality_review import BindingError,build_assertion_view,digest
from test_attribution_review import artifacts


def encoded(value):
    return json.dumps(value,ensure_ascii=False).encode()


class ModalityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        quote = 'Se notificaron 3 casos probables.'
        possible_quote = 'Podrían haberse notificado otros 2 casos probables.'
        fixture = artifacts(quote=quote, extra=' ' + possible_quote,
                            metric_name='casos probables')
        cls.payload = json.loads(fixture['claims_bytes'])
        first = cls.payload['claims'][0]
        first['metric']['value_text'] = '3'
        second = deepcopy(first)
        second.update(claim_id='constructed-possible', polarity='uncertain',
                      summary=possible_quote)
        second['metric'].update(value_numeric=2, value_text='2')
        second['evidence'][0]['text'] = possible_quote
        cls.payload['claims'].append(second)
        cls.source = fixture['raw_text']
        cls.schema = fixture['claims_schema']

    def args(self,payload=None,modalities=('asserted','possible')):
        cb=encoded(self.payload if payload is None else payload)
        entries=[dict(claim_pointer=f'/claims/{i}',modality=m,reviewer='constructed test author',
            review_kind='constructed_control',evidence_pointer=f'/claims/{i}/evidence/0') for i,m in enumerate(modalities)]
        ab=encoded(dict(version='offline-modality-annotation-draft-1',claims_sha256=digest(cb),
            source_sha256=digest(self.source.encode()),entries=entries))
        return dict(claims_bytes=cb,claims_sha256=digest(cb),source_text=self.source,
            source_sha256=digest(self.source.encode()),annotation_bytes=ab,annotation_sha256=digest(ab),claims_schema=self.schema,
            expected_document=deepcopy((self.payload if payload is None else payload)["document"]))

    def test_preserves_mixed_values_and_class_without_total(self):
        result=build_assertion_view(**self.args())
        self.assertEqual([a['metric']['value_numeric'] for a in result['assertions']],[3,2])
        self.assertEqual([a['modality'] for a in result['assertions']],['asserted','possible'])
        self.assertTrue(all(a['metric']['name']=='casos probables' for a in result['assertions']))
        self.assertIsNone(result['aggregate'])

    def test_equal_metrics_keep_distinct_claim_identities(self):
        payload=deepcopy(self.payload)
        payload['claims'][1]['metric']=deepcopy(payload['claims'][0]['metric'])
        result=build_assertion_view(**self.args(payload))
        self.assertEqual(len(result['assertions']),2)
        self.assertNotEqual(result['assertions'][0]['assertion_id'],result['assertions'][1]['assertion_id'])
        self.assertEqual([a['modality'] for a in result['assertions']],['asserted','possible'])

    def test_unannotated_is_not_evaluated_even_with_positive_polarity(self):
        result=build_assertion_view(**self.args(modalities=()))
        self.assertEqual([a['modality'] for a in result['assertions']],['not_evaluated']*2)
        self.assertTrue(all(a['modality_annotation'] is None for a in result['assertions']))

    def test_no_mutation_or_aliasing(self):
        args=self.args(); before=deepcopy(args)
        result=build_assertion_view(**args)
        self.assertEqual(args,before)
        result['assertions'][0]['original_claim']['polarity']='negative'
        result['assertions'][0]['metric']['value_numeric']=999
        self.assertEqual(build_assertion_view(**args)['assertions'][0]['metric']['value_numeric'],3)

    def test_deterministic_ids_change_with_artifact_version(self):
        result=build_assertion_view(**self.args())
        self.assertEqual(result,build_assertion_view(**self.args()))
        changed=deepcopy(self.payload); changed['warnings'].append('new artifact version')
        other=build_assertion_view(**self.args(changed))
        self.assertNotEqual(result['assertions'][0]['assertion_id'],other['assertions'][0]['assertion_id'])

    def test_claim_and_source_and_annotation_hashes_are_required(self):
        for field in ('claims_sha256','source_sha256','annotation_sha256'):
            with self.subTest(field=field):
                args=self.args(); args[field]='0'*64
                with self.assertRaises(BindingError):build_assertion_view(**args)

    def mutate_annotations(self,change):
        args=self.args(); annotations=json.loads(args['annotation_bytes']); change(annotations)
        args['annotation_bytes']=encoded(annotations); args['annotation_sha256']=digest(args['annotation_bytes'])
        return args

    def test_rejects_stale_binding_even_with_updated_annotation_hash(self):
        args=self.mutate_annotations(lambda a:a.update(claims_sha256='0'*64))
        with self.assertRaises(BindingError):build_assertion_view(**args)

    def test_rejects_conflicting_annotations_instead_of_picking_one(self):
        def conflict(a):
            other=deepcopy(a['entries'][0]); other['modality']='possible'; a['entries'].append(other)
        with self.assertRaises(BindingError):build_assertion_view(**self.mutate_annotations(conflict))

    def test_rejects_unmatched_annotation(self):
        args=self.mutate_annotations(lambda a:a['entries'][0].update(claim_pointer='/claims/99'))
        with self.assertRaises(BindingError):build_assertion_view(**args)

    def test_rejects_annotation_evidence_from_another_claim(self):
        args=self.mutate_annotations(lambda a:a['entries'][0].update(evidence_pointer='/claims/1/evidence/0'))
        with self.assertRaises(BindingError):build_assertion_view(**args)

    def test_nonmetric_claim_retained_without_synthetic_zero(self):
        payload=deepcopy(self.payload)
        payload['claims'][1]['metric'].update(reported=False,value_numeric=None,value_text=None)
        result=build_assertion_view(**self.args(payload,('asserted',)))
        self.assertEqual(len(result['assertions']),1)
        self.assertEqual(len(result['nonmetric_claims']),1)
        self.assertIsNone(result['nonmetric_claims'][0]['claim']['metric']['value_numeric'])

    def test_cannot_annotate_a_nonmetric_claim(self):
        payload=deepcopy(self.payload); payload['claims'][1]['metric'].update(reported=False,value_numeric=None,value_text=None)
        with self.assertRaises(BindingError):build_assertion_view(**self.args(payload))

    def test_negative_polarity_can_coexist_with_asserted_zero(self):
        payload=deepcopy(self.payload)
        payload['claims']=payload['claims'][:1]
        c=payload['claims'][0]; c['polarity']='negative'; c['metric'].update(name='casos confirmados',value_numeric=0,value_text='0')
        c['evidence'][0]['text']='Se notificaron 0 casos confirmados.'
        args=self.args(payload,('asserted',)); args['source_text']=c['evidence'][0]['text']; args['source_sha256']=digest(args['source_text'].encode())
        annotations=json.loads(args['annotation_bytes']); annotations['source_sha256']=args['source_sha256']
        args['annotation_bytes']=encoded(annotations); args['annotation_sha256']=digest(args['annotation_bytes'])
        result=build_assertion_view(**args)
        self.assertEqual(result['assertions'][0]['metric']['value_numeric'],0)
        self.assertEqual(result['assertions'][0]['modality'],'asserted')
        self.assertEqual(result['assertions'][0]['original_claim']['polarity'],'negative')

    def test_invalid_explicit_state_and_schema_and_literal_rejected(self):
        with self.assertRaises(BindingError):build_assertion_view(**self.args(modalities=('certain',)))
        payload=deepcopy(self.payload); del payload['claims'][0]['metric']
        with self.assertRaises(BindingError):build_assertion_view(**self.args(payload))
        payload=deepcopy(self.payload); payload['claims'][0]['evidence'][0]['text']='Invented quote.'
        with self.assertRaises(BindingError):build_assertion_view(**self.args(payload))

    def test_whitespace_only_evidence_rejected(self):
        payload=deepcopy(self.payload); payload['claims'][0]['evidence'][0]['text']='  \n '
        with self.assertRaises(BindingError):build_assertion_view(**self.args(payload))

    def test_malformed_annotation_state_rejected(self):
        args=self.mutate_annotations(lambda a:a['entries'][0].update(modality=[]))
        with self.assertRaises(BindingError):build_assertion_view(**args)


    def test_explicit_document_binding_rejects_other_metadata(self):
        args=self.args();args['expected_document']['language']='en'
        with self.assertRaises(BindingError):build_assertion_view(**args)
        args=self.args();args['expected_document']=None
        with self.assertRaises(BindingError):build_assertion_view(**args)

    def test_external_schema_reference_rejected_without_resolution(self):
        args=self.args();args['claims_schema']=deepcopy(self.schema)
        args['claims_schema']['$ref']='https://invalid.example/no-network-schema'
        with self.assertRaises(BindingError):build_assertion_view(**args)

    def test_duplicate_json_keys_rejected_even_when_last_value_is_valid(self):
        for field, hash_field, key in (
            ('claims_bytes', 'claims_sha256', 'document'),
            ('annotation_bytes', 'annotation_sha256', 'version'),
        ):
            with self.subTest(field=field):
                args = self.args()
                original = args[field]
                value = json.loads(original)[key]
                duplicate = ('{' + json.dumps(key) + ':' + json.dumps(value) + ',').encode()
                args[field] = duplicate + original[1:]
                args[hash_field] = digest(args[field])
                with self.assertRaises(BindingError):
                    build_assertion_view(**args)

    def test_overflowed_json_number_rejected(self):
        args = self.args()
        payload = json.loads(args['claims_bytes'])
        payload['claims'][0]['metric']['value_numeric'] = 'overflow-marker'
        args['claims_bytes'] = encoded(payload).replace(b'"overflow-marker"', b'1e999')
        args['claims_sha256'] = digest(args['claims_bytes'])
        annotations = json.loads(args['annotation_bytes'])
        annotations['claims_sha256'] = args['claims_sha256']
        args['annotation_bytes'] = encoded(annotations)
        args['annotation_sha256'] = digest(args['annotation_bytes'])
        with self.assertRaises(BindingError):
            build_assertion_view(**args)

    def test_annotation_revision_preserves_assertion_and_original_identity(self):
        before = build_assertion_view(**self.args())
        after = build_assertion_view(**self.args(modalities=('possible', 'asserted')))
        self.assertNotEqual(before['annotation_sha256'], after['annotation_sha256'])
        for first, second in zip(before['assertions'], after['assertions']):
            self.assertEqual(first['assertion_id'], second['assertion_id'])
            self.assertEqual(first['original_claim'], second['original_claim'])
            self.assertEqual(first['metric'], second['metric'])
            self.assertNotEqual(first['modality'], second['modality'])

    def test_whitespace_normalized_literal_evidence_remains_valid(self):
        args = self.args()
        args['source_text'] = args['source_text'].replace(' ', '\n')
        args['source_sha256'] = digest(args['source_text'].encode())
        annotations = json.loads(args['annotation_bytes'])
        annotations['source_sha256'] = args['source_sha256']
        args['annotation_bytes'] = encoded(annotations)
        args['annotation_sha256'] = digest(args['annotation_bytes'])
        result = build_assertion_view(**args)
        self.assertEqual(len(result['assertions']), 2)

    def test_partial_annotation_keeps_other_metric_not_evaluated(self):
        result = build_assertion_view(**self.args(modalities=('asserted',)))
        self.assertEqual([row['modality'] for row in result['assertions']],
                         ['asserted', 'not_evaluated'])
        self.assertEqual([row['metric']['value_numeric'] for row in result['assertions']], [3, 2])

    def test_stale_annotation_source_rejected_with_valid_source_and_artifact_hashes(self):
        args = self.mutate_annotations(lambda a: a.update(source_sha256='0' * 64))
        with self.assertRaises(BindingError):
            build_assertion_view(**args)

    def test_unknown_annotation_version_and_extra_fields_rejected(self):
        for change in (lambda a: a.update(version='future-unrecognized-format'),
                       lambda a: a.update(automatic_acceptance=True)):
            with self.subTest(change=change):
                with self.assertRaises(BindingError):
                    build_assertion_view(**self.mutate_annotations(change))


if __name__=='__main__':
    unittest.main(verbosity=2)
