.PHONY: api run-uvicorn
api:
	@python retrieval_api.py

run-uvicorn:
	@python -m uvicorn retrieval_api:app --reload --host 0.0.0.0 --port 8000
