import { useState, useRef, useEffect } from "react";
import * as faceapi from "face-api.js";
import "./UploadFace.css";

export default function UploadFace() {
  const [userId, setUserId] = useState("");
  const [cameraActive, setCameraActive] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [faceCentered, setFaceCentered] = useState(false);
  const [currentMoveIndex, setCurrentMoveIndex] = useState(-1);
  const [statusMessage, setStatusMessage] = useState("");
  const [resultMessage, setResultMessage] = useState("");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const rafRef = useRef(null);

  const CENTER_TOLERANCE = 0.22;
  const movementSequence = ["ESQUERDA", "DIREITA"];
  const framesPerMove = 5;
  const frameInterval = 400;

  const startCamera = async () => {
    if (!userId) return alert("Informe o ID do Usuário");
    setCameraActive(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      });
      videoRef.current.srcObject = stream;
      streamRef.current = stream;
      await videoRef.current.play();

      if ("FaceDetector" in window) {
        detectorRef.current = new window.FaceDetector({
          fastMode: true,
          maxDetectedFaces: 1,
        });
        detectLoopNative();
      } else {
        await faceapi.nets.tinyFaceDetector.loadFromUri("/models");
        detectLoopFaceApi();
      }
    } catch (err) {
      alert("Erro ao acessar câmera: " + err.message);
      setCameraActive(false);
    }
  };

  const detectLoopNative = async () => {
    const detectFrame = async () => {
      if (!detectorRef.current || !videoRef.current) {
        rafRef.current = requestAnimationFrame(detectFrame);
        return;
      }
      try {
        const faces = await detectorRef.current.detect(videoRef.current);
        if (faces.length > 0) {
          const box = faces[0].boundingBox;
          const nx = (box.x + box.width / 2) / videoRef.current.videoWidth;
          const ny = (box.y + box.height / 2) / videoRef.current.videoHeight;
          setFaceDetected(true);
          setFaceCentered(
            Math.abs(nx - 0.5) <= CENTER_TOLERANCE &&
            Math.abs(ny - 0.5) <= CENTER_TOLERANCE
          );
        } else {
          setFaceDetected(false);
          setFaceCentered(false);
        }
      } catch {
        setFaceDetected(false);
        setFaceCentered(false);
      } finally {
        rafRef.current = requestAnimationFrame(detectFrame);
      }
    };
    detectFrame();
  };

  const detectLoopFaceApi = async () => {
    const detectFrame = async () => {
      if (!videoRef.current) return;
      const detection = await faceapi.detectSingleFace(
        videoRef.current,
        new faceapi.TinyFaceDetectorOptions()
      );
      if (detection) {
        const box = detection.box;
        const nx = (box.x + box.width / 2) / videoRef.current.videoWidth;
        const ny = (box.y + box.height / 2) / videoRef.current.videoHeight;
        setFaceDetected(true);
        setFaceCentered(
          Math.abs(nx - 0.5) <= CENTER_TOLERANCE &&
          Math.abs(ny - 0.5) <= CENTER_TOLERANCE
        );
      } else {
        setFaceDetected(false);
        setFaceCentered(false);
      }
      rafRef.current = requestAnimationFrame(detectFrame);
    };
    detectFrame();
  };

  useEffect(() => {
    if (faceCentered && currentMoveIndex === -1) {
      setCurrentMoveIndex(0);
    }
  }, [faceCentered]);

  useEffect(() => {
    const captureMove = async () => {
      if (currentMoveIndex === -1 || currentMoveIndex >= movementSequence.length)
        return;

      setStatusMessage(movementSequence[currentMoveIndex]);

      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      canvas.width = videoRef.current.videoWidth || 640;
      canvas.height = videoRef.current.videoHeight || 480;

      const frames = [];
      for (let f = 0; f < framesPerMove; f++) {
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(videoRef.current, -canvas.width, 0, canvas.width, canvas.height);
        ctx.restore();
        const blob = await new Promise((res) =>
          canvas.toBlob(res, "image/jpeg", 0.9)
        );
        if (blob)
          frames.push(
            new File(
              [blob],
              `frame_${movementSequence[currentMoveIndex]}_${f}_${Date.now()}.jpg`,
              { type: "image/jpeg" }
            )
          );
        await new Promise((r) => setTimeout(r, frameInterval));
      }

      if (!canvas.framesCollected) canvas.framesCollected = [];
      canvas.framesCollected.push(...frames);

      await new Promise((r) => setTimeout(r, 800));

      const nextIndex = currentMoveIndex + 1;
      if (nextIndex < movementSequence.length) {
        setCurrentMoveIndex(nextIndex);
      } else {
        setStatusMessage("Salvando imagens...");
        await captureFinalResult();
        setCurrentMoveIndex(movementSequence.length);
      }
    };

    captureMove();
  }, [currentMoveIndex]);

  const captureFinalResult = async () => {
    const formData = new FormData();
    canvasRef.current.framesCollected.forEach((f) =>
      formData.append("files", f)
    );

    try {
      const res = await fetch(`http://localhost:8000/faces/upload/${userId}`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      await res.json();

      setResultMessage("Upload finalizado com sucesso!");
    } catch (err) {
      setResultMessage("Erro ao salvar imagens: " + err.message);
    } finally {
      setStatusMessage("");
      canvasRef.current.framesCollected = [];
    }
  };

  const stopAll = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    detectorRef.current = null;
    setCameraActive(false);
    setFaceDetected(false);
    setFaceCentered(false);
    setCurrentMoveIndex(-1);
    setStatusMessage("");
    setResultMessage("");
  };

  useEffect(() => () => stopAll(), []);

  const renderArrowMessage = () => {
    if (!faceDetected) return "Rosto não detectado";
    if (faceDetected && !faceCentered) return "Centralize seu rosto";
    if (faceCentered && statusMessage === "ESQUERDA")
      return (
        <div className="arrow-message">
          <span className="arrow-icon">←</span>
          <span>Mova o rosto para a esquerda</span>
        </div>
      );
    if (faceCentered && statusMessage === "DIREITA")
      return (
        <div className="arrow-message">
          <span className="arrow-icon">→</span>
          <span>Mova o rosto para a direita</span>
        </div>
      );
    return statusMessage;
  };

  return (
    <div className="upload-card">
      <h2>Cadastro de Liveness Facial</h2>
      <input
        type="text"
        placeholder="ID do Usuário"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />

      {!cameraActive && (
        <button className="start-button" onClick={startCamera} disabled={!userId}>
          Ativar Câmera
        </button>
      )}

      {cameraActive && (
        <div className="video-wrapper">
          <video ref={videoRef} autoPlay playsInline muted />

          {/* Desfoque oval */}
          <div className="blur-overlay" />

          {/* Moldura oval */}
          <div className="face-frame" />

          <div className="arrow-overlay">{renderArrowMessage()}</div>

          <div className="button-overlay">
            <button className="start-button stop" onClick={stopAll}>
              Parar
            </button>
          </div>
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: "none" }} />

      {resultMessage && <div className="result">{resultMessage}</div>}
    </div>
  );
}
