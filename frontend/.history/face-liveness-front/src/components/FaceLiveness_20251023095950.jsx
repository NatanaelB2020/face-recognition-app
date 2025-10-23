import { useState, useRef, useEffect } from "react";
import * as faceapi from "face-api.js";
import "./FaceLiveness.css";

export default function FaceLiveness() {
  const [userId, setUserId] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [faceCentered, setFaceCentered] = useState(false);
  const [faceDetected, setFaceDetected] = useState(false);
  const [usingFaceApi, setUsingFaceApi] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [currentFrame, setCurrentFrame] = useState(0);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const detectorRef = useRef(null);
  const rafRef = useRef(null);

  const movementSequence = ["ESQUERDA", "DIREITA"];
  const framesPerMove = 10;
  const frameInterval = 400;
  const CENTER_TOLERANCE = 0.22;

  // --- Início da câmera ---
  const startCamera = async () => {
    if (!userId) return alert("Informe o ID do Usuário");
    setCameraActive(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
      videoRef.current.srcObject = stream;
      streamRef.current = stream;
      await videoRef.current.play();

      if ("FaceDetector" in window) {
        try {
          detectorRef.current = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 1 });
          startDetectLoopNative();
        } catch {
          startFaceApiFallback();
        }
      } else {
        startFaceApiFallback();
      }
    } catch (err) {
      alert("Erro ao acessar câmera: " + err.message);
      setCameraActive(false);
    }
  };

  // --- Detecção nativa ---
  const startDetectLoopNative = () => {
    const detectFrame = async () => {
      if (!detectorRef.current || !videoRef.current) {
        rafRef.current = requestAnimationFrame(detectFrame);
        return;
      }
      try {
        const faces = await detectorRef.current.detect(videoRef.current);
        if (faces.length > 0) {
          const box = faces[0].boundingBox;
          const nx = (box.x + box.width / 2) / (videoRef.current.videoWidth || 640);
          const ny = (box.y + box.height / 2) / (videoRef.current.videoHeight || 480);
          setFaceDetected(true);
          setFaceCentered(Math.abs(nx - 0.5) <= CENTER_TOLERANCE && Math.abs(ny - 0.5) <= CENTER_TOLERANCE);
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
    rafRef.current = requestAnimationFrame(detectFrame);
  };

  // --- Fallback: face-api.js ---
  const startFaceApiFallback = async () => {
    setUsingFaceApi(true);
    await faceapi.nets.tinyFaceDetector.loadFromUri("/models");
    const detectFrame = async () => {
      if (!videoRef.current) return;
      const detection = await faceapi.detectSingleFace(videoRef.current, new faceapi.TinyFaceDetectorOptions());
      if (detection) {
        setFaceDetected(true);
        const box = detection.box;
        const nx = (box.x + box.width / 2) / videoRef.current.videoWidth;
        const ny = (box.y + box.height / 2) / videoRef.current.videoHeight;
        setFaceCentered(Math.abs(nx - 0.5) <= CENTER_TOLERANCE && Math.abs(ny - 0.5) <= CENTER_TOLERANCE);
      } else {
        setFaceDetected(false);
        setFaceCentered(false);
      }
      rafRef.current = requestAnimationFrame(detectFrame);
    };
    detectFrame();
  };

  // --- Captura da sequência ---
  const captureLivenessSequence = async () => {
    if (!faceCentered) return alert("Centralize seu rosto antes de iniciar o teste.");
    if (!videoRef.current || !canvasRef.current || !userId) return;

    setLoading(true);
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;

    const allFrames = [];

    for (let step = 0; step < movementSequence.length; step++) {
      setCurrentStep(step);
      setCurrentFrame(0);

      for (let f = 0; f < framesPerMove; f++) {
        setCurrentFrame(f + 1);
        ctx.save();
        ctx.scale(-1, 1);
        ctx.drawImage(videoRef.current, -canvas.width, 0, canvas.width, canvas.height);
        ctx.restore();
        const blob = await new Promise((res) => canvas.toBlob(res, "image/jpeg", 0.9));
        if (blob)
          allFrames.push(
            new File([blob], `frame_${movementSequence[step]}_${f}_${Date.now()}.jpg`, { type: "image/jpeg" })
          );
        await new Promise((r) => setTimeout(r, frameInterval));
      }
    }

    setCurrentStep(-1);
    setCurrentFrame(0);

    const formData = new FormData();
    allFrames.forEach((f) => formData.append("files", f));

    try {
      const res = await fetch(`http://localhost:8000/faces/liveness/${userId}`, { method: "POST", body: formData });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResponse(data);
      alert(`Teste de liveness concluído! Resultado: ${JSON.stringify(data.status || "OK")}`);
    } catch (err) {
      alert("Erro ao enviar dados: " + err.message);
    } finally {
      setLoading(false);
      allFrames.length = 0;
    }
  };

  // --- Parar e limpar ---
  const stopAll = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    detectorRef.current = null;
    setCameraActive(false);
    setFaceCentered(false);
    setFaceDetected(false);
  };

  useEffect(() => () => stopAll(), []);

  return (
    <div className="upload-card">
      <h2>Verificação de Liveness Facial</h2>
      <input type="text" placeholder="ID do Usuário" value={userId} onChange={(e) => setUserId(e.target.value)} />

      <div className="button-group" style={{ marginBottom: 12 }}>
        {!cameraActive && (
          <button className="start-button" onClick={startCamera} disabled={loading || !userId}>
            Ativar Câmera
          </button>
        )}

        {cameraActive && (
          <>
            <button
              className="start-button"
              onClick={captureLivenessSequence}
              disabled={loading || !faceCentered}
            >
              {loading
                ? "Analisando..."
                : faceCentered
                ? "Iniciar Teste de Liveness"
                : "Aguardando centralização..."}
            </button>
            <button
              className="start-button"
              onClick={stopAll}
              style={{ background: "#f44336", marginLeft: 8 }}
            >
              Parar
            </button>
          </>
        )}
      </div>

      {cameraActive && (
        <div className="video-wrapper" style={{ position: "relative" }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            width="640"
            height="480"
            style={{ borderRadius: 8, transform: "scaleX(-1)", backgroundColor: "#000" }}
          />

          <div className="face-frame" />

          <div
            className="arrow-overlay"
            style={{
              top: 12,
              left: "50%",
              transform: "translateX(-50%)",
              backgroundColor: faceDetected
                ? faceCentered
                  ? "rgba(46,170,65,0.85)"
                  : "rgba(255,165,0,0.9)"
                : "rgba(220,20,60,0.9)",
            }}
          >
            {faceDetected
              ? faceCentered
                ? "Rosto centralizado"
                : "Ajuste seu rosto ao centro"
              : "Rosto não detectado"}
          </div>

          {currentStep >= 0 && (
            <div
              className="movement-instruction"
              style={{
                position: "absolute",
                bottom: 20,
                left: "50%",
                transform: "translateX(-50%)",
                padding: "8px 16px",
                borderRadius: 8,
                backgroundColor: "rgba(0,0,0,0.6)",
                color: "#fff",
                fontSize: 18,
              }}
            >
              Mova para: {movementSequence[currentStep]} ({currentFrame}/{framesPerMove})
            </div>
          )}
        </div>
      )}

      <canvas ref={canvasRef} style={{ display: "none" }} />

      {response && (
        <div className="result" style={{ marginTop: 12 }}>
          <h4>Resultado do Teste:</h4>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
