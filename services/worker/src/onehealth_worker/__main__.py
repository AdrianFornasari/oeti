from .config import Settings


def main() -> None:
    settings = Settings()
    print("One Health worker configurado.")
    print(f"Supabase: {settings.supabase_url}")
    print("Pipeline de ingesta: pendiente del siguiente sprint.")


if __name__ == "__main__":
    main()
