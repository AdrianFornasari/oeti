export const mvHondiusBenchmark = {
  caseCode: "ARG-HANTA-MV-HONDIUS-2026",
  benchmarkVersion: "0.4",
  architecture: "atomic_claims_v0.1+deterministic_signal_assembly_v0.4.4",
  documentCount: 6,
  releaseThresholds: {
    meanSignalF1: 0.9,
    meanEvidenceSupportF1: 0.9,
    meanSignalRoleAccuracy: 0.9,
    meanSignalTypeAccuracy: 0.85,
  },
  documents: [
    { date: "04 May 2026", label: "Initial notification and national monitoring", source: "ARG_MSAL_NEWS", relation: "MV Hondius monitoring" },
    { date: "12 May 2026", label: "BEN epidemiological bulletin — SE17", source: "ARG_MSAL_NEWS", relation: "MV Hondius monitoring" },
    { date: "19 May 2026", label: "BEN epidemiological bulletin — SE18", source: "ARG_MSAL_NEWS", relation: "MV Hondius monitoring" },
    { date: "26 May 2026", label: "BEN epidemiological bulletin — SE19", source: "ARG_MSAL_NEWS", relation: "MV Hondius monitoring" },
    { date: "29 Jun 2026", label: "Tierra del Fuego rodents — genomic evidence not related to the outbreak", source: "ARG_ANLIS_NEWS", relation: "Negative causal evidence" },
    { date: "08 Jul 2026", label: "Mendoza rodents — negative evidence", source: "ARG_ANLIS_NEWS", relation: "Negative evidence" },
  ],
} as const;

export const ushuaiaRodentSignal = {
  id: "8b333d10-4ef2-4aa3-b61b-ccd1f2ab3784-asm-01",
  shortId: "ASM-01",
  schemaVersion: "0.4",
  documentDate: "29 Jun 2026",
  signalRole: "primary_event",
  signalType: "laboratory_result",
  domains: ["wildlife"],
  pathogen: "Hantavirus",
  host: "Abrothrix",
  location: {
    country: "Argentina",
    admin1: "Tierra del Fuego",
    locality: "Ushuaia",
    precision: "locality",
    confidence: 0.86,
    role: "sampling_location",
  },
  eventDate: null,
  metric: { name: "seropositive_animals", value: 5, unit: "animals" },
  diagnostics: { testType: "serología", target: "anticuerpos específicos", result: "positive" },
  verificationStatus: "reported",
  extractionConfidence: 0.8,
  summary: "Cinco roedores del género Abrothrix presentaron anticuerpos específicos contra hantavirus en Ushuaia (Tierra del Fuego).",
  evidence: "Los resultados obtenidos mostraron que cinco ejemplares pertenecientes al género Abrothrix presentaron anticuerpos específicos contra hantavirus.",
  source: {
    code: "ARG_ANLIS_NEWS",
    label: "ANLIS-Malbrán — official news",
    url: "https://www.argentina.gob.ar/noticias/anlis-malbran-identifico-hantavirus-en-roedores-de-tierra-del-fuego-sin-relacion-con-el-0",
  },
  directClaim: {
    id: "c1",
    kind: "diagnostic_result",
    polarity: "positive",
    confidence: 0.8,
  },
} as const;

export const ushuaiaRodentContext = {
  genomicSignal: {
    id: "8b333d10-4ef2-4aa3-b61b-ccd1f2ab3784-asm-02",
    type: "genomic_observation",
    summary: "Molecular analyses identified a previously undescribed hantavirus variant related to Andes virus and classified within Orthohantavirus andesense.",
  },
  causalNegativeSignal: {
    id: "8b333d10-4ef2-4aa3-b61b-ccd1f2ab3784-asm-03",
    role: "negative_evidence",
    type: "transmission_observation",
    summary: "The investigation ruled out the analysed rodents as the source of infection linked to the MV Hondius event.",
    evidence: "De esta manera, la investigación permitió descartar que los roedores analizados hayan sido la fuente de infección vinculada a ese evento.",
    animalToHuman: "refuted",
    claimId: "c4",
  },
  samplingSignal: {
    id: "8b333d10-4ef2-4aa3-b61b-ccd1f2ab3784-asm-04",
    type: "wildlife_event",
    start: "18 May 2026",
    end: "22 May 2026",
    capturedRodents: 144,
    summary: "During field operations between 18 and 22 May, 144 wild rodents were captured.",
    claimId: "c5",
  },
} as const;
