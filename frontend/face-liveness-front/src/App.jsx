import { useState, useRef } from "react";
import UploadFace from "./components/UploadFace";
import FaceLiveness from "./components/FaceLiveness";
import SidebarMenu from "./components/SidebarMenu";

export default function App() {
  const [activePage, setActivePage] = useState("upload");
  const [collapsed, setCollapsed] = useState(false);
  const livenessRef = useRef(null);

  const handlePageChange = (newPage) => {
    if (activePage === "liveness" && livenessRef.current?.forceStopCamera) {
      livenessRef.current.forceStopCamera();
      setTimeout(() => setActivePage(newPage), 100);
    } else {
      setActivePage(newPage);
    }
  };

  return (
    <div className="App min-h-screen flex flex-col">
      {/* Cabeçalho */}
      <header className="bg-[#36495B] text-white p-3 flex items-center justify-between shadow-md sticky top-0 z-10">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="bg-transparent text-white hover:bg-gray-600 px-2 py-1 text-sm"
        >
          {collapsed ? "☰" : "✖"}
        </button>
      </header>

      {/* Layout principal */}
      <div className="flex flex-1 overflow-hidden">
        {/* Menu lateral */}
        <SidebarMenu
          activePage={activePage}
          setActivePage={handlePageChange}
          collapsed={collapsed}
        />

        {/* Conteúdo centralizado */}
        <main className="flex-1 flex justify-center items-center overflow-auto bg-gray-50 p-4">
          {activePage === "upload" && <UploadFace />}
          {activePage === "liveness" && <FaceLiveness ref={livenessRef} />}
        </main>
      </div>

      {/* Rodapé */}
      <footer className="bg-gray-900 text-gray-500 text-xs p-2 text-center border-t border-gray-700 flex-shrink-0">
        © 2025 Demonstração. Todos os direitos reservados.
      </footer>
    </div>
  );
}
