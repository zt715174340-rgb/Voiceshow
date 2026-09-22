"""Streaming ASR/TTS orchestration. Pseudocode only."""

async def process_audio(socket, user):
    asr = asr_client.start_stream()
    tts = tts_client.start_stream()
    async for chunk in socket:
        text = await asr.push(chunk)
        if is_final_text(text):
            answer = await orchestrator.handle(user.session, text)
            for sentence in sentence_split(answer.text):
                await socket.send_bytes(await tts.synthesize(sentence))
