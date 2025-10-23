# test_liveness.py
import psutil
import os
import time
from datetime import datetime

from app.data.database import get_db, Base, engine
from app.model.user import User
from app.model.face import Face
from app.services.face_liveness_service import check_face_liveness_visual


def log_performance(result, elapsed_time, mem_diff_mb, cpu_user, cpu_system):
    """
    Registra as métricas de desempenho em um arquivo de log.
    """
    log_file = "liveness_metrics.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n==============================\n")
        f.write(f"Data e hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tempo total: {elapsed_time:.2f} segundos\n")
        f.write(f"Memória usada: {mem_diff_mb:.2f} MB\n")
        f.write(f"CPU (user): {cpu_user:.2f}s | CPU (system): {cpu_system:.2f}s\n")
        f.write(f"Resultado do liveness: {result}\n")
        f.write("==============================\n")


def main():
    Base.metadata.create_all(bind=engine)
    db = next(get_db())

    user_id = 1
    face_id = 10
    threshold = 0.8
    movements_required = 2
    frames_to_capture = 60

    print("==> Iniciando teste de liveness. Use a câmera e mova a cabeça!")

    # Coleta inicial de uso de CPU e memória
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_times()
    mem_before = process.memory_info().rss
    start_time = time.time()

    # Execução real do reconhecimento facial
    result = check_face_liveness_visual(
        db=db,
        user_id=user_id,
        face_id=face_id,
        threshold=threshold,
        movements_required=movements_required,
        frames_to_capture=frames_to_capture
    )

    # Coleta final e cálculo
    end_time = time.time()
    cpu_after = process.cpu_times()
    mem_after = process.memory_info().rss

    elapsed_time = end_time - start_time
    mem_diff_mb = (mem_after - mem_before) / (1024 * 1024)
    cpu_user = cpu_after.user - cpu_before.user
    cpu_system = cpu_after.system - cpu_before.system

    print("\n==> Resultado do liveness:")
    print(result)

    print("\n==> Métricas de desempenho:")
    print(f"Tempo total: {elapsed_time:.2f} segundos")
    print(f"Memória usada: {mem_diff_mb:.2f} MB")
    print(f"CPU (user): {cpu_user:.2f}s | CPU (system): {cpu_system:.2f}s")

    # 🪶 Registrar métricas no arquivo
    log_performance(result, elapsed_time, mem_diff_mb, cpu_user, cpu_system)
    print(f"\n Métricas registradas em 'liveness_metrics.log'")


if __name__ == "__main__":
    main()
