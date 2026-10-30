from pathlib import Path
import re
import unittest

PROJECT = Path(__file__).parents[1]
PROFILE = PROJECT / "profiles" / "motorcycle.lua"
DOCKERFILE = PROJECT / "Dockerfile"
PUBLISH_WORKFLOW = PROJECT / ".github" / "workflows" / "publish-image.yml"


class MotorcycleProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PROFILE.read_text()

    def test_motorcycle_access_precedes_generic_vehicle_access(self):
        block = re.search(r"access_tags_hierarchy\s*=\s*Sequence\s*\{([^}]*)\}", self.source, re.S)
        self.assertIsNotNone(block)
        tags = re.findall(r"'([^']+)'", block.group(1))
        self.assertEqual(tags, ["motorcycle", "motor_vehicle", "vehicle", "access"])

    def test_car_only_access_tag_is_not_whitelisted_or_prioritized(self):
        self.assertNotRegex(self.source, r"access_tags_hierarchy\s*=\s*Sequence\s*\{[^}]*'motorcar'")
        self.assertNotRegex(self.source, r"access_tag_whitelist\s*=\s*Set\s*\{[^}]*'motorcar'")

    def test_motorway_and_toll_roads_are_explicitly_avoided(self):
        block = re.search(r"avoid\s*=\s*Set\s*\{([^}]*)\}", self.source, re.S)
        self.assertIsNotNone(block)
        tags = re.findall(r"'([^']+)'", block.group(1))
        self.assertIn("motorway", tags)
        self.assertIn("motorway_link", tags)
        self.assertIn("toll", tags)


class DockerImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = DOCKERFILE.read_text()

    def test_build_downloads_and_checks_osm_data_then_extracts_region(self):
        self.assertIn("OSM_PBF_URL", self.source)
        self.assertIn("OSM_PBF_MD5_URL", self.source)
        self.assertIn("md5sum -c", self.source)
        self.assertIn("osmium extract", self.source)

    def test_source_pbf_is_not_copied_from_project_context_or_final_image(self):
        self.assertNotRegex(self.source, r"(?m)^COPY\s+data/.*\.osm\.pbf")
        self.assertIn("COPY --from=osm-extract /data/bojonegoro-tuban.osm.pbf", self.source)
        self.assertIn("rm -f /data/*.osm.pbf", self.source)
        self.assertIn("COPY --from=graph-builder /data/ /data/", self.source)

    def test_osrm_license_notice_is_not_ignored_by_git(self):
        gitignore = (PROJECT / ".gitignore").read_text()
        self.assertIn("!LICENSE.OSRM", gitignore)
        self.assertIn("LICENSE.OSRM", self.source)

    def test_github_action_publishes_image_using_github_token(self):
        workflow = PUBLISH_WORKFLOW.read_text()
        self.assertIn("packages: write", workflow)
        self.assertIn("secrets.GITHUB_TOKEN", workflow)
        self.assertIn("ghcr.io/nuralan/osrm-motorcycle-router", workflow)
        self.assertIn("docker/build-push-action", workflow)
        self.assertIn("OSM_PBF_URL=", workflow)




if __name__ == "__main__":
    unittest.main()
