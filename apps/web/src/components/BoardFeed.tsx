import React, { useRef, useEffect, useState } from "react";
import type { Detection, Observation } from "../types";

const FEED_SIZE = 500;

const PLAYER_COLORS: Record<string, string> = {
  japan: "#c0392b",
  usa: "#2980b9",
  uk_pacific: "#27ae60",
  anzac: "#e67e22",
  china: "#f39c12",
};

const CONFIDENCE_COLORS: Record<string, string> = {
  high: "#55efc4",
  medium: "#ffeaa7",
  low: "#e17055",
  very_low: "#d63031",
};

interface Props {
  observation: Observation | null;
  isCalibrated: boolean;
  wsConnected: boolean;
}

export default function BoardFeed({ observation, isCalibrated, wsConnected }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraActive, setCameraActive] = useState(false);

  useEffect(() => {
    if (!navigator.mediaDevices?.getUserMedia) return;
    let stream: MediaStream | null = null;
    let cancelled = false;

    navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
    })
      .then((s) => {
        if (cancelled) { s.getTracks().forEach((t) => t.stop()); return; }
        stream = s;
        setCameraActive(true);
      })
      .catch(() => setCameraActive(false));

    return () => {
      cancelled = true;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Attach stream to video element once both are available
  useEffect(() => {
    if (!cameraActive || !videoRef.current) return;
    navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: "environment" } },
    }).then((s) => {
      if (videoRef.current) {
        videoRef.current.srcObject = s;
      }
    }).catch(() => {});
  }, [cameraActive]);

  const detections = observation?.detections ?? [];
  const overallConfidence = observation?.overall_confidence ?? "low";

  return (
    <div className="board-feed-wrapper">
      {/* Status badges */}
      <div style={{ position: "absolute", top: 12, left: 12, zIndex: 10, display: "flex", gap: 8 }}>
        <Badge
          color={wsConnected ? "#55efc4" : "#e17055"}
          label={wsConnected ? "LIVE" : "OFFLINE"}
        />
        {cameraActive && <Badge color="#55efc4" label="CAMERA" />}
        {isCalibrated && <Badge color="#74b9ff" label="CALIBRATED" />}
        {detections.length > 0 && (
          <Badge
            color={CONFIDENCE_COLORS[overallConfidence]}
            label={`${detections.length} detections`}
          />
        )}
      </div>

      {/* Video element — always in DOM so ref is valid */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          objectFit: "cover",
          borderRadius: 12,
          opacity: cameraActive ? 1 : 0,
          transition: "opacity 0.4s ease",
        }}
      />

      {/* Placeholder shown on top when camera is not active */}
      {!cameraActive && <PlaceholderBoard />}

      {/* Detection overlay */}
      {detections.length > 0 && (
        <svg
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "none",
          }}
          viewBox={`0 0 ${FEED_SIZE} ${FEED_SIZE}`}
          preserveAspectRatio="none"
        >
          {detections.map((d) => (
            <DetectionBox
              key={d.detection_id}
              detection={d}
              containerWidth={FEED_SIZE}
              containerHeight={FEED_SIZE}
            />
          ))}
        </svg>
      )}
    </div>
  );
}

function PlaceholderBoard() {
  return (
    <div style={{
      position: "absolute",
      inset: 0,
      background: "linear-gradient(135deg, #0a0e1a 0%, #131a2e 50%, #0a0e1a 100%)",
      borderRadius: 12,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      gap: 12,
    }}>
      <div style={{ fontSize: 48, opacity: 0.15 }}>&#127909;</div>
      <div style={{ color: "#555", fontSize: 14, fontWeight: 600 }}>
        Camera Feed
      </div>
      <div style={{ color: "#3a3a5e", fontSize: 12, maxWidth: 280, textAlign: "center" }}>
        Connect a camera to enable board detection. The vision module will overlay
        detected units and zone assignments here.
      </div>
    </div>
  );
}

function DetectionBox({
  detection,
  containerWidth,
  containerHeight,
}: {
  detection: Detection;
  containerWidth: number;
  containerHeight: number;
}) {
  const { bbox, owner, unit_type, overall_confidence, confidence_band } = detection;
  const color = owner ? (PLAYER_COLORS[owner] ?? "#55efc4") : "#55efc4";
  const x = (bbox.x1 / 1920) * containerWidth;
  const y = (bbox.y1 / 1080) * containerHeight;
  const w = ((bbox.x2 - bbox.x1) / 1920) * containerWidth;
  const h = ((bbox.y2 - bbox.y1) / 1080) * containerHeight;

  return (
    <g>
      <rect
        x={x} y={y} width={w} height={h}
        fill="none"
        stroke={color}
        strokeWidth={2}
        rx={3}
        opacity={0.85}
      />
      {unit_type && (
        <text
          x={x + 3}
          y={y - 4}
          fill={color}
          fontSize={10}
          fontFamily="system-ui"
          fontWeight={600}
        >
          {unit_type} {(overall_confidence * 100).toFixed(0)}%
        </text>
      )}
      <circle
        cx={x + w - 4}
        cy={y + 4}
        r={3}
        fill={CONFIDENCE_COLORS[confidence_band]}
      />
    </g>
  );
}

function Badge({ color, label }: { color: string; label: string }) {
  return (
    <div style={{
      background: "rgba(0,0,0,0.6)",
      border: `1px solid ${color}`,
      color,
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 10,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: 0.5,
      backdropFilter: "blur(4px)",
    }}>
      {label}
    </div>
  );
}
