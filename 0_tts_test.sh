source .env
curl -sS https://api.openai.com/v1/audio/speech -X POST \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini-tts","voice":"alloy","input":"This class is pretty hard","response_format":"mp3"}' \
  --output say.mp3