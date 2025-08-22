from fastapi import APIRouter, HTTPException
from app.api.models import TableState, GTOResponse
from app.advisor.texas_solver_client import TexasSolverClient

router = APIRouter()
_client = TexasSolverClient()

@router.post("/solver/nhle_decide", response_model=GTOResponse)
def solver_decide(state: TableState) -> GTOResponse:
    ts = _client.solve(state)
    if ts.get("status") != "ok":
        raise HTTPException(status_code=502, detail={"upstream": ts})
    return _client.to_gto_response(state, ts)
