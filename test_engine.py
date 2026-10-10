import sys, tempfile, unittest
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import engine as e


class ModelTests(unittest.TestCase):
    def test_scores_bounded(self):
        for r in (0, 50, 100):
            for b in (0, 50, 100):
                for t in (0, 100):
                    for i in e.INTERVENTIONS:
                        s = e.simulate(r, b, t, i, report_pressure=1)
                        self.assertTrue(all(0 <= v <= 1 for v in s.values()))

    def test_every_intervention_helps_or_is_neutral(self):
        base = e.worst_downstream(e.simulate(75, 85, 65))
        for i in e.INTERVENTIONS[1:]:
            self.assertLessEqual(e.worst_downstream(e.simulate(75, 85, 65, i)), base + 1e-9)

    def test_clear_drain_cuts_blockage(self):
        self.assertLess(e.simulate(75, 85, 65, "Clear the critical drain")["Drain blockage"],
                        e.simulate(75, 85, 65)["Drain blockage"])

    def test_pumps_reduce_rain_effect_only_for_pumps(self):
        a = e.simulate(75, 85, 65)["Street flooding"]
        b = e.simulate(75, 85, 65, "Deploy temporary water pumps")["Street flooding"]
        c = e.simulate(75, 85, 65, "Reroute traffic early")["Street flooding"]
        self.assertLess(b, a); self.assertAlmostEqual(a, c)

    def test_report_pressure_raises_flood(self):
        self.assertGreater(e.simulate(40, 40, 40, report_pressure=1)["Street flooding"],
                           e.simulate(40, 40, 40)["Street flooding"])

    def test_trigger_and_ranking(self):
        t, _ = e.top_trigger(e.simulate(20, 95, 50)); self.assertEqual(t, "Drain blockage")
        df = e.rank_interventions(75, 85, 65)
        self.assertEqual(len(df), 5)
        self.assertEqual(df.iloc[0]["Worst downstream index"], df["Worst downstream index"].min())


class WeatherTests(unittest.TestCase):
    def payload(self):
        times = [f"2026-10-10T{h:02d}:00" for h in range(24)]
        return {"current": {"time": "2026-10-10T12:15", "precipitation": 1.0},
                "hourly": {"time": times,
                           "precipitation": [0.0]*9 + [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] + [0.0]*9,
                           "precipitation_probability": [10]*12 + [80, 60, 30] + [0]*9}}

    def test_window(self):
        w = e.parse_weather(self.payload())
        past, fut, prob = e.rainfall_window(w["hourly"], w["now"], 3, 3)
        self.assertAlmostEqual(past, 1 + 2 + 3)      # hours 9,10,11
        self.assertAlmostEqual(fut, 4 + 5 + 6)       # hours 12,13,14
        self.assertEqual(prob, 80)

    def test_empty(self):
        w = e.parse_weather({})
        self.assertEqual(e.rainfall_window(w["hourly"], w["now"]), (0.0, 0.0, None))


class GeoTests(unittest.TestCase):
    def test_haversine(self):
        self.assertAlmostEqual(e.haversine_m(17.0, 79.0, 17.0, 79.0), 0, places=3)
        self.assertAlmostEqual(e.haversine_m(0, 0, 0, 1), 111195, delta=200)

    def test_fmt(self):
        self.assertEqual(e.fmt_distance(340), "340 m"); self.assertEqual(e.fmt_distance(2500), "2.5 km")


class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(); self.p = Path(self.dir.name) / "i.csv"
    def tearDown(self): self.dir.cleanup()

    def test_roundtrip_and_status(self):
        rid = e.save_incident(self.p, "Blocked drain", " water rising ", "High", 17.97, 79.59, " Market ")
        df = e.load_incidents(self.p)
        self.assertEqual(len(df), 1); self.assertEqual(df.iloc[0]["description"], "water rising")
        self.assertTrue(e.update_status(self.p, rid, "Resolved"))
        self.assertEqual(e.load_incidents(self.p).iloc[0]["status"], "Resolved")
        self.assertFalse(e.update_status(self.p, "nope", "Resolved"))

    def test_legacy_csv_migrates(self):
        old = "reported_at,incident_type,description,severity,latitude,longitude,area,status\n" \
              "2026-10-10T10:00:00+05:30,Other hazard,x,Low,17.9,79.5,y,Unverified — needs review\n"
        self.p.write_text(old, encoding="utf-8")
        e.save_incident(self.p, "Other hazard", "new", "Low", 17.9, 79.5, "z")
        df = e.load_incidents(self.p)
        self.assertEqual(len(df), 2); self.assertTrue((df["report_id"] != "").all())
        self.assertEqual(df["report_id"].nunique(), 2)

    def test_pressure(self):
        e.save_incident(self.p, "Blocked drain", "a", "Critical", 17.9, 79.5, "x")
        e.save_incident(self.p, "Blocked drain", "b", "High", 17.9, 79.5, "x")
        df = e.load_incidents(self.p)
        self.assertAlmostEqual(e.report_pressure(df), 1.8 / 3)
        old = df.copy(); old["reported_at"] = (datetime.now().astimezone() - timedelta(hours=48)).isoformat()
        self.assertEqual(e.report_pressure(old), 0.0)
        self.assertEqual(e.report_pressure(pd.DataFrame(columns=e.INCIDENT_COLUMNS)), 0.0)



class V3Tests(unittest.TestCase):
    def hourly(self):
        t = pd.date_range("2026-10-10 00:00", periods=48, freq="h")
        mm = [0.0] * 12 + [4.0] * 6 + [0.0] * 30
        return pd.DataFrame({"time": t, "precip_mm": mm, "precip_prob": [50] * 48})

    def test_timeline_and_crossing(self):
        tl = e.risk_timeline(self.hourly(), pd.Timestamp("2026-10-10 10:30"), 85, 65, "Clear the critical drain")
        self.assertFalse(tl.empty)
        self.assertTrue((tl["With intervention"] <= tl["Baseline"] + 1e-9).all())
        self.assertIsNotNone(e.first_crossing(tl, "Baseline", 40))
        self.assertIsNone(e.first_crossing(tl, "Baseline", 1000))
        self.assertTrue(e.risk_timeline(pd.DataFrame(columns=["time", "precip_mm", "precip_prob"]), pd.NaT, 1, 1).empty)

    def test_ground_truth(self):
        self.assertIn("no recent reports", e.ground_truth_note("HIGH", 0))
        self.assertIn("missing", e.ground_truth_note("LOW", 3))
        self.assertIn("same way", e.ground_truth_note("HIGH", 2))

    def test_demo_seed_and_delete(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "i.csv"
            e.save_incident(p, "Other hazard", "real one", "Low", 1, 1, "x")
            self.assertEqual(e.seed_demo_reports(p, 17.9, 79.5), 4)
            self.assertEqual(len(e.load_incidents(p)), 5)
            self.assertEqual(e.delete_demo_reports(p), 4)
            self.assertEqual(len(e.load_incidents(p)), 1)

    def test_sitrep(self):
        b = e.simulate(75, 85, 65); a = e.simulate(75, 85, 65, "Clear the critical drain")
        txt = e.build_sitrep("X", "now", 75, False, 85, 65, b, a, "Clear the critical drain", "Drain blockage",
                             "HIGH", 0, pd.DataFrame(columns=e.INCIDENT_COLUMNS), None, None)
        self.assertIn("ILLUSTRATIVE", txt); self.assertIn("HIGH", txt)

if __name__ == "__main__":
    unittest.main()
