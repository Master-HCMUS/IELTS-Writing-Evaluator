from fastapi.testclient import TestClient

from app.main import app
from app.validation.schemas import validate_score_response

client = TestClient(app)


def test_score_task2_minimal() -> None:
	essay = """Many cities today face severe congestion and declining air quality. Some people argue that increasing the price of fuel is the most effective way to solve these problems. While higher fuel costs can immediately discourage unnecessary car journeys, I believe a broader package of measures delivers more sustainable and fair outcomes.

	First, pricing can shape behavior, but it is a blunt instrument. Sharp fuel hikes disproportionately affect low-income commuters who have limited access to reliable public transport. If governments rely on fuel taxes alone, they risk punishing people who must drive for work, healthcare, or caregiving. Instead, targeted policies—such as congestion charges that vary by time and location—more precisely reduce peak traffic without penalizing essential trips in off-peak hours.

	Second, improving alternatives is crucial. When cities invest in frequent buses, protected cycling lanes, and safe sidewalks, residents naturally switch modes. For example, integrated ticketing and real-time information reduce friction, while park-and-ride facilities extend the reach of rail. Complementary policies like employer-backed transit passes, last-mile micromobility, and secure bike parking further shift habits. Over time, these investments lower household transport costs and enhance equity.

	Third, land-use reforms matter as much as transport policy. Zoning that allows mixed-use, medium-density neighborhoods shortens daily journeys and enables walking by design. Requiring new developments to unbundle parking and provide transit access nudges people toward cleaner choices without heavy-handed bans. In parallel, electrifying public fleets and incentivizing clean delivery vehicles reduce pollution from trips that must still occur.

	In conclusion, raising fuel prices can play a supporting role, but it is neither a silver bullet nor a just solution on its own. Cities should combine modest, predictable pricing signals with ambitious improvements to public transport, safe cycling networks, walkable planning, and clean fleets. This integrated approach tackles congestion and pollution while expanding opportunity for everyone."""
	req = {"task_type": "task2", "essay": essay}
	r = client.post("/score", json=req)
	assert r.status_code == 200, r.text
	resp = r.json()
	# Validate the response against schema
	validate_score_response(resp)
	assert resp["overall"] in [4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
	assert len(resp["votes"]) == 3
	assert resp["confidence"] in ["high", "low"]


def test_score_rejects_short_task2() -> None:
	essay = "This response is intentionally brief and does not meet the exam requirement of at least two hundred and fifty words."
	req = {"task_type": "task2", "essay": essay}
	r = client.post("/score", json=req)
	assert r.status_code == 400
	assert "at least 250 words" in r.text


def test_score_rejects_task1_in_phase1() -> None:
	essay = """Many cities today face severe congestion and declining air quality. Some people argue that increasing the price of fuel is the most effective way to solve these problems. While higher fuel costs can immediately discourage unnecessary car journeys, I believe a broader package of measures delivers more sustainable and fair outcomes.

	First, pricing can shape behavior, but it is a blunt instrument. Sharp fuel hikes disproportionately affect low-income commuters who have limited access to reliable public transport. If governments rely on fuel taxes alone, they risk punishing people who must drive for work, healthcare, or caregiving. Instead, targeted policies—such as congestion charges that vary by time and location—more precisely reduce peak traffic without penalizing essential trips in off-peak hours.

	Second, improving alternatives is crucial. When cities invest in frequent buses, protected cycling lanes, and safe sidewalks, residents naturally switch modes. For example, integrated ticketing and real-time information reduce friction, while park-and-ride facilities extend the reach of rail. Complementary policies like employer-backed transit passes, last-mile micromobility, and secure bike parking further shift habits. Over time, these investments lower household transport costs and enhance equity.

	Third, land-use reforms matter as much as transport policy. Zoning that allows mixed-use, medium-density neighborhoods shortens daily journeys and enables walking by design. Requiring new developments to unbundle parking and provide transit access nudges people toward cleaner choices without heavy-handed bans. In parallel, electrifying public fleets and incentivizing clean delivery vehicles reduce pollution from trips that must still occur.

	In conclusion, raising fuel prices can play a supporting role, but it is neither a silver bullet nor a just solution on its own. Cities should combine modest, predictable pricing signals with ambitious improvements to public transport, safe cycling networks, walkable planning, and clean fleets. This integrated approach tackles congestion and pollution while expanding opportunity for everyone."""
	req = {"task_type": "task1", "essay": essay}
	r = client.post("/score", json=req)
	assert r.status_code == 400
