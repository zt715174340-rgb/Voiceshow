"""Server-side streaming ASR/TTS boundary. Pseudocode only."""

async def voice_session(socket, user):
    session_id = await open_session(user.id)
    asr = asr_client.start_stream()
    tts = tts_client.start_stream()

    async for event in socket:
        if event.type == "audio_chunk":
            partial = await asr.push(event.bytes)
            await socket.send_json({"type": "asr_partial", "text": partial})
        elif event.type == "speech_end":
            query = await asr.finalize()
            result = await graph.ainvoke({"session_id": session_id, "query": query})
            for sentence in sentence_split(result.answer):
                await socket.send_bytes(await tts.synthesize(sentence))
            await socket.send_json({"type": "answer_end"})
