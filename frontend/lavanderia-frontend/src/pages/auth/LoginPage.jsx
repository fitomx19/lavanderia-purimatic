import React, { useState } from 'react';
import './LoginPage.css';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../../services/login';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);

    try {
      const response = await loginUser(username, password);
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      const role = response.data.user?.role;
      navigate(role === 'empleado' ? '/sales' : '/dashboard');
    } catch (err) {
      setError(err.message || 'Error de conexión');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-layout">
      <div className="login-panel">
        <div className="login-brand">
          <p className="login-brand-name">Lavandería Purimatic</p>
          <h1>Iniciar sesión</h1>
          <p className="login-help">Accede con tu usuario de tienda para continuar.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="username">
            Usuario
            <input
              type="text"
              id="username"
              name="username"
              autoComplete="username"
              placeholder="Tu usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>

          <label htmlFor="password">
            Contraseña
            <input
              type="password"
              id="password"
              name="password"
              autoComplete="current-password"
              placeholder="Tu contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-submit" disabled={busy}>
            {busy ? 'Entrando…' : 'Entrar'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
