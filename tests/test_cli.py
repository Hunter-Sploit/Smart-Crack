import pytest
from smartcrack.config import load_config, set_default_wordlist, reset_config, get_settings, Settings


class TestConfig:
    def setup_method(self):
        reset_config()

    def test_default_config(self):
        cfg = load_config()
        assert cfg["default_wordlist"] is None
        assert cfg["timeout_seconds"] == 3600
        assert "wordlists" in cfg
        assert cfg["wordlists"] == []

    def test_set_wordlist(self):
        set_default_wordlist("test_wordlist.txt")
        cfg = load_config()
        assert cfg["default_wordlist"] == "test_wordlist.txt"
        assert "test_wordlist.txt" in cfg["wordlists"]

    def test_pydantic_settings(self):
        settings = get_settings()
        assert settings.timeout_seconds == 3600
        assert ".smartcrack" in settings.session_dir
        assert settings.wordlists == []

    def test_migration_from_json(self):
        # Create old-style JSON config
        import json
        from pathlib import Path
        from smartcrack.config.settings import _settings
        config_dir = Path.home() / ".smartcrack"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.json"
        old_config = {
            "default_wordlist": "/old/path/wordlist.txt",
            "wordlists": ["/old/wordlist1.txt", "/old/wordlist2.txt"],
            "preferred_backend": "hashcat",
            "timeout_seconds": 7200,
            "session_dir": "/old/sessions"
        }
        config_path.write_text(json.dumps(old_config))

        try:
            # Force re-load to test migration
            import smartcrack.config.settings as settings_module
            settings_module._settings = None
            cfg = load_config()
            assert cfg["default_wordlist"] == "/old/path/wordlist.txt"
            assert cfg["wordlists"] == ["/old/wordlist1.txt", "/old/wordlist2.txt"]
            assert cfg["preferred_tool"] == "hashcat"
            assert cfg["timeout_seconds"] == 7200
        finally:
            config_path.unlink(missing_ok=True)
            # Reset global
            settings_module._settings = None

    def test_reset_config(self):
        set_default_wordlist("wordlist_sample.txt")
        cfg = reset_config()
        assert cfg["default_wordlist"] is None
        assert cfg["wordlists"] == []


class TestIdentifier:
    def test_md5(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("5f4dcc3b5aa765d61d8327deb882cf99")
        assert len(candidates) >= 2
        names = [c.name for c in candidates]
        assert "MD5" in names
        assert "NTLM" in names
        md5 = next(c for c in candidates if c.name == "MD5")
        assert md5.hashcat_mode == 0
        assert md5.john_format == "raw-md5"

    def test_sha1(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8")
        names = [c.name for c in candidates]
        assert "SHA1" in names
        assert "RIPEMD-160" in names
        sha1 = next(c for c in candidates if c.name == "SHA1")
        assert sha1.hashcat_mode == 100

    def test_sha256(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("5e884898da28047151d0e56f8dc62927845f5c520a550de58b9c47af9ad8e217")
        names = [c.name for c in candidates]
        assert "SHA256" in names
        sha256 = next(c for c in candidates if c.name == "SHA256")
        assert sha256.hashcat_mode == 1400

    def test_bcrypt(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u")
        names = [c.name for c in candidates]
        assert "bcrypt" in names
        bcrypt = next(c for c in candidates if c.name == "bcrypt")
        assert bcrypt.hashcat_mode == 3200
        assert bcrypt.confidence > 0.9

    def test_ntlm(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("8846f7eaee8fb117ad06bdd830b7586c")
        names = [c.name for c in candidates]
        assert "MD5" in names
        assert "NTLM" in names

    def test_mysql(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19")
        names = [c.name for c in candidates]
        assert "MySQL 5.7+" in names
        mysql = next(c for c in candidates if c.name == "MySQL 5.7+")
        assert mysql.hashcat_mode == 7401

    def test_salted_md5(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("6a204bd8bce90f2a3a9e90a6e47213f8:salt")
        names = [c.name for c in candidates]
        assert "MD5 (salted)" in names
        assert "vBulletin" in names
        salted = next(c for c in candidates if c.name == "MD5 (salted)")
        assert salted.hashcat_mode == 10

    def test_sha256_crypt(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("$5$salt$eGSigWJlPyHPltF4wY2i7kcD/dANpwKG7hOPOjYL7B5:salt")
        names = [c.name for c in candidates]
        assert "sha256crypt" in names
        sha256crypt = next(c for c in candidates if c.name == "sha256crypt")
        assert sha256crypt.hashcat_mode == 7400

    def test_oracle(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("EA4D5C2B1672CC9B1567490471E8F67DFF2D4487B2B91948")
        names = [c.name for c in candidates]
        assert "Oracle 10g/11g" in names
        oracle = next(c for c in candidates if c.name == "Oracle 10g/11g")
        assert oracle.hashcat_mode == 3100

    def test_commands_included(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("5f4dcc3b5aa765d61d8327deb882cf99", "rockyou.txt")
        md5 = next(c for c in candidates if c.name == "MD5")
        assert hasattr(md5, "commands")
        assert "hashcat" in md5.commands
        assert "john" in md5.commands
        assert "-m 0" in md5.commands["hashcat"]
        assert "rockyou.txt" in md5.commands["hashcat"]

    def test_unknown_hash(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("not_a_hash_at_all")
        assert len(candidates) == 0 or (len(candidates) == 1 and candidates[0].name == "Unknown Hex")

    def test_confidence_ordering(self):
        from smartcrack.identifiers.hash_identifier import identify_hash
        candidates = identify_hash("$2b$12$Yzk7dXbKj.0.EKjEpqgvN.8EhY2x3QUBgLhK5E1V0sJl1p7qFRx3u")
        assert candidates[0].confidence >= candidates[1].confidence if len(candidates) > 1 else True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])