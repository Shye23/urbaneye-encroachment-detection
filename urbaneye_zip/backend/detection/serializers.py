from datetime import date

from rest_framework import serializers

from .models import DetectionArtifact, DetectionCandidate, DetectionJob


class DetectionCandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionCandidate
        fields = (
            "id",
            "candidate_id",
            "status",
            "geometry",
            "attributes",
        )


class DetectionArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionArtifact
        fields = ("id", "kind", "name", "path")


class DetectionJobSerializer(serializers.ModelSerializer):
    candidates = DetectionCandidateSerializer(many=True, read_only=True)
    artifacts = DetectionArtifactSerializer(many=True, read_only=True)

    class Meta:
        model = DetectionJob
        fields = (
            "id",
            "aoi",
            "start_date",
            "end_date",
            "collection",
            "status",
            "progress",
            "error_message",
            "scene_metadata",
            "result_summary",
            "created_at",
            "started_at",
            "completed_at",
            "candidates",
            "artifacts",
        )
        read_only_fields = fields


class DetectionJobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetectionJob
        fields = ("aoi", "start_date", "end_date", "collection")

    def validate_aoi(self, value):
        if not isinstance(value, dict) or value.get("type") not in {
            "Feature",
            "FeatureCollection",
            "Polygon",
            "MultiPolygon",
        }:
            raise serializers.ValidationError(
                "aoi must be a GeoJSON Feature, FeatureCollection, Polygon, or MultiPolygon."
            )
        return value

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError(
                {"end_date": "end_date must be after start_date."}
            )
        if (attrs["end_date"] - attrs["start_date"]).days > 366 * 10:
            raise serializers.ValidationError(
                {"end_date": "The requested date range cannot exceed ten years."}
            )
        return attrs
