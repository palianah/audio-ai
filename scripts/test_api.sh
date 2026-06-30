#!/bin/bash
# Quick API test — run after docker compose up
VID="86b328b452b7"
S1="e806ed60c200"
S2="7425658ece8b"

echo "=== Apply ==="
curl -s -X POST -H "Content-Type: application/json" \
  -d "{\"video_id\":\"$VID\",\"stem_results\":[{\"stem_id\":\"$S1\",\"offset_ms\":10150,\"matched_face_id\":1,\"overall_confidence\":0.889,\"segment_maps\":[{\"audio_start_s\":1.472,\"audio_end_s\":4.576,\"lip_start_s\":11.7,\"lip_end_s\":14.3,\"stretch_ratio\":0.8376,\"confidence\":0.835},{\"audio_start_s\":4.992,\"audio_end_s\":9.408,\"lip_start_s\":15.1,\"lip_end_s\":20.6,\"stretch_ratio\":1.2455,\"confidence\":0.7}],\"notes\":[]},{\"stem_id\":\"$S2\",\"offset_ms\":10150,\"matched_face_id\":1,\"overall_confidence\":0.889,\"segment_maps\":[{\"audio_start_s\":1.472,\"audio_end_s\":4.576,\"lip_start_s\":11.7,\"lip_end_s\":14.3,\"stretch_ratio\":0.8376,\"confidence\":0.835}],\"notes\":[]}]}" \
  http://localhost:8000/api/sync/apply

echo ""
echo "=== Preview URL ==="
echo "http://localhost:8000/api/sync/preview/$VID"
echo ""
echo "Open this URL in your browser to hear the synced audio!"
