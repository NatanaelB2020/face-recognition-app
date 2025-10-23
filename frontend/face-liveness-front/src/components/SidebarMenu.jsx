import React from "react";
import "./SidebarMenu.css";

const MenuItem = ({ page, icon, label, activePage, onClick }) => {
  const isActive = activePage === page;
  return (
    <button
      className={`menu-button ${isActive ? "menu-button-active" : ""}`}
      onClick={() => onClick(page)}
    >
      <div className="menu-icon">{icon}</div>
      <span className="menu-label">{label}</span>
    </button>
  );
};

export default function SidebarMenu({ activePage, setActivePage, collapsed }) {
  const handlePageChange = (page) => setActivePage(page);

  return (
    <nav className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
      <MenuItem
        page="liveness"
        label="Liveness (Câmera)"
        activePage={activePage}
        onClick={handlePageChange}
      />
      <MenuItem
        page="upload"
        label="Upload de Face"
        activePage={activePage}
        onClick={handlePageChange}
      />
    </nav>
  );
}
