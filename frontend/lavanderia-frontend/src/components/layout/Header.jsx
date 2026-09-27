import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import './Header.css';

const getStoredUser = () => {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = getStoredUser();
  const isAdmin = user?.role === 'admin';
  const [adminOpen, setAdminOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const adminRef = useRef(null);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
  };

  const go = (path) => {
    setAdminOpen(false);
    setMobileOpen(false);
    navigate(path);
  };

  useEffect(() => {
    const onDocClick = (event) => {
      if (adminRef.current && !adminRef.current.contains(event.target)) {
        setAdminOpen(false);
      }
    };
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  useEffect(() => {
    setAdminOpen(false);
    setMobileOpen(false);
  }, [location.pathname]);

  const isActive = (path) => location.pathname === path;

  const userLabel = user?.name || user?.username || user?.email || 'Usuario';
  const roleLabel = user?.role === 'admin' ? 'Admin' : user?.role === 'empleado' ? 'Empleado' : '';

  return (
    <header className="app-header">
      <div className="app-header-inner">
        <button type="button" className="app-brand" onClick={() => go(isAdmin ? '/dashboard' : '/sales')}>
          Lavandería Purimatic
        </button>

        <nav className="app-header-nav" aria-label="Navegación principal">
          <button
            type="button"
            className={`header-nav-link header-nav-link--primary ${isActive('/sales') ? 'is-active' : ''}`}
            onClick={() => go('/sales')}
          >
            Ventas
          </button>
          <button
            type="button"
            className={`header-nav-link ${isActive('/recargas') ? 'is-active' : ''}`}
            onClick={() => go('/recargas')}
          >
            Recargas
          </button>
          <button
            type="button"
            className={`header-nav-link ${isActive('/transactions') ? 'is-active' : ''}`}
            onClick={() => go('/transactions')}
          >
            Historial
          </button>
          <button
            type="button"
            className={`header-nav-link ${isActive('/encargos') ? 'is-active' : ''}`}
            onClick={() => go('/encargos')}
          >
            Encargos
          </button>

          {isAdmin && (
            <>
              <button
                type="button"
                className={`header-nav-link ${isActive('/dashboard') ? 'is-active' : ''}`}
                onClick={() => go('/dashboard')}
              >
                Dashboard
              </button>

              <div className="header-dropdown" ref={adminRef}>
                <button
                  type="button"
                  className={`header-nav-link header-dropdown-toggle ${adminOpen ? 'is-open' : ''} ${
                    isActive('/esp32-config') ||
                    isActive('/ticket-settings') ||
                    isActive('/encargos-precios') ||
                    isActive('/card-benefits')
                      ? 'is-active'
                      : ''
                  }`}
                  onClick={() => setAdminOpen((open) => !open)}
                  aria-expanded={adminOpen}
                  aria-haspopup="true"
                >
                  Administración
                  <span className="header-caret" aria-hidden="true" />
                </button>
                {adminOpen && (
                  <div className="header-dropdown-menu" role="menu">
                    <button type="button" role="menuitem" onClick={() => go('/esp32-config')}>
                      Placas ESP32
                    </button>
                    <button type="button" role="menuitem" onClick={() => go('/ticket-settings')}>
                      Ticket 80mm
                    </button>
                    <button type="button" role="menuitem" onClick={() => go('/encargos-precios')}>
                      Precios encargos
                    </button>
                    <button type="button" role="menuitem" onClick={() => go('/card-benefits')}>
                      Beneficios tarjeta
                    </button>
                  </div>
                )}
              </div>
            </>
          )}
        </nav>

        <div className="app-header-actions">
          <div className="header-user">
            <span className="header-user-name">{userLabel}</span>
            {roleLabel && <span className="header-user-role">{roleLabel}</span>}
          </div>
          <button type="button" onClick={handleLogout} className="header-logout-button">
            Cerrar sesión
          </button>
          <button
            type="button"
            className="header-menu-toggle"
            aria-label="Abrir menú"
            aria-expanded={mobileOpen}
            onClick={() => setMobileOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="app-header-mobile" role="navigation" aria-label="Menú móvil">
          <button
            type="button"
            className={`header-mobile-link ${isActive('/sales') ? 'is-active' : ''}`}
            onClick={() => go('/sales')}
          >
            Ventas
          </button>
          <button
            type="button"
            className={`header-mobile-link ${isActive('/recargas') ? 'is-active' : ''}`}
            onClick={() => go('/recargas')}
          >
            Recargas
          </button>
          <button
            type="button"
            className={`header-mobile-link ${isActive('/transactions') ? 'is-active' : ''}`}
            onClick={() => go('/transactions')}
          >
            Historial
          </button>
          <button
            type="button"
            className={`header-mobile-link ${isActive('/encargos') ? 'is-active' : ''}`}
            onClick={() => go('/encargos')}
          >
            Encargos
          </button>
          {isAdmin && (
            <>
              <button
                type="button"
                className={`header-mobile-link ${isActive('/dashboard') ? 'is-active' : ''}`}
                onClick={() => go('/dashboard')}
              >
                Dashboard
              </button>
              <button
                type="button"
                className={`header-mobile-link ${isActive('/esp32-config') ? 'is-active' : ''}`}
                onClick={() => go('/esp32-config')}
              >
                Placas ESP32
              </button>
              <button
                type="button"
                className={`header-mobile-link ${isActive('/ticket-settings') ? 'is-active' : ''}`}
                onClick={() => go('/ticket-settings')}
              >
                Ticket 80mm
              </button>
              <button
                type="button"
                className={`header-mobile-link ${isActive('/encargos-precios') ? 'is-active' : ''}`}
                onClick={() => go('/encargos-precios')}
              >
                Precios encargos
              </button>
              <button
                type="button"
                className={`header-mobile-link ${isActive('/card-benefits') ? 'is-active' : ''}`}
                onClick={() => go('/card-benefits')}
              >
                Beneficios tarjeta
              </button>
            </>
          )}
          <button type="button" className="header-mobile-logout" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      )}
    </header>
  );
};

export default Header;
