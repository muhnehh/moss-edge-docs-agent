import argparse
import asyncio
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agent.chat_agent import MossEdgeAgent

load_dotenv()


class MossVoiceAgent:
    def __init__(
        self,
        stt_model: str = "gpt-4o-mini-transcribe",
        tts_model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for voice mode.")

        self.openai = AsyncOpenAI(api_key=api_key)
        self.agent = MossEdgeAgent()
        self.stt_model = stt_model
        self.tts_model = tts_model
        self.voice = voice

    async def transcribe_audio(self, audio_path: Path) -> str:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with audio_path.open("rb") as audio_file:
            transcription = await self.openai.audio.transcriptions.create(
                model=self.stt_model,
                file=audio_file,
            )

        text = getattr(transcription, "text", "")
        return text.strip()

    async def synthesize_speech(self, text: str, output_audio: Path) -> Path:
        output_audio.parent.mkdir(parents=True, exist_ok=True)

        speech = await self.openai.audio.speech.create(
            model=self.tts_model,
            voice=self.voice,
            input=text,
        )

        if hasattr(speech, "write_to_file"):
            speech.write_to_file(str(output_audio))
        elif hasattr(speech, "content"):
            output_audio.write_bytes(speech.content)
        else:
            raise RuntimeError("Unsupported speech response type from OpenAI SDK.")

        return output_audio

    async def answer_from_audio(
        self,
        input_audio: Path,
        output_audio: Path | None = None,
    ) -> dict[str, Any]:
        question = await self.transcribe_audio(input_audio)
        if not question:
            raise RuntimeError("Transcription returned empty text.")

        result = await self.agent.answer(question)

        audio_out = None
        if output_audio:
            audio_out = await self.synthesize_speech(result["answer"], output_audio)

        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "timings": result["timings"],
            "output_audio": str(audio_out) if audio_out else None,
        }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run voice-query flow for Moss Edge Agent.")
    parser.add_argument("--input-audio", required=True, help="Path to input audio file.")
    parser.add_argument(
        "--output-audio",
        default="data/voice/answer.mp3",
        help="Path to synthesized output audio file.",
    )
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Skip text-to-speech generation and print text-only answer.",
    )
    args = parser.parse_args()

    agent = MossVoiceAgent(
        stt_model=os.getenv("OPENAI_STT_MODEL", "gpt-4o-mini-transcribe"),
        tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        voice=os.getenv("OPENAI_TTS_VOICE", "alloy"),
    )

    result = await agent.answer_from_audio(
        input_audio=Path(args.input_audio),
        output_audio=None if args.no_tts else Path(args.output_audio),
    )

    print("\nTranscribed question:")
    print(result["question"])
    print("\nAnswer:")
    print(result["answer"])
    print("\nSources:")
    print(result["sources"])
    print("\nTimings:")
    print(result["timings"])
    if result["output_audio"]:
        print(f"\nAudio answer written to: {result['output_audio']}")


if __name__ == "__main__":
    asyncio.run(main())
