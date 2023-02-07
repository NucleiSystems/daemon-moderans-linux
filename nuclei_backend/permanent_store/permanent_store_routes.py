import typing
from fastapi import Depends, File, Form, HTTPException, UploadFile, status

from . import permanent_store_model
from .main import permanent_store_router

from .chunking import Reconstruct, scan_for_ccif_files
from .file_handlers import FileDigestion, NormaliseFile

from ..users.auth_utils import get_current_user
from ..users.user_handler_utils import get_db


@permanent_store_router.post("/info_test")
def info_test(
    # make token a body parameter
    token: str = Form(...),
):
    return {"message": token}


@permanent_store_model.post("/digest_files")
async def file_digestion(
    files: typing.List[UploadFile] = File(...),
):
    try:
        for file in files:
            FileDigestion(file).digest()
            NormaliseFile(file).run()
            FileDigestion(file).remove()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e,
        ) from e

    return {"message": "File digested successfully"}


@permanent_store_router.get("/rebuild_all")
async def rebuild_all(token=Depends()):
    # check for jwt token

    for file in scan_for_ccif_files():
        reconstruct_controller = Reconstruct(file)
        reconstruct_controller.run()

    return {"message": "All files reconstructed successfully"}
