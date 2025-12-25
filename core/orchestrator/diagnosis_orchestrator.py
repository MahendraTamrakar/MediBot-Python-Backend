class DiagnosisOrchestrator:
    def __init__(self, ocr, diagnosis, compliance):
        self.ocr = ocr
        self.diagnosis = diagnosis
        self.compliance = compliance

    async def process(self, file_path: str):
        text = await self.ocr.run(file_path)
        diagnosis = await self.diagnosis.run(text)
        return await self.compliance.run(diagnosis)
