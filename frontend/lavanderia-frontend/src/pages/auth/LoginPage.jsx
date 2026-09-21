import React, { useState } from 'react';
import './LoginPage.css';
import { useNavigate } from 'react-router-dom';
import { loginUser } from '../../services/login';

const LoginPage = () => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('AdminPurimatic2024');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Limpiar errores anteriores

    try {
      const response = await loginUser(username, password);
      console.log('Autenticación exitosa:', response);
      localStorage.setItem('token', response.data.token); // Guardar el token
      localStorage.setItem('user', JSON.stringify(response.data.user)); // Guardar datos del usuario (incluye el rol)

      // Redirigir según el rol: el empleado solo tiene acceso a Ventas e Historial
      const role = response.data.user?.role;
      navigate(role === 'empleado' ? '/sales' : '/dashboard');

    } catch (err) {
      console.error('Error de autenticación:', err);
      setError(err.message || 'Error de conexión');
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h2>Iniciar Sesión</h2>
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label htmlFor="username">Usuario:</label>
            <input
              type="text"
              id="username"
              name="username"
              placeholder="Ingresa tu usuario"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="input-group">
            <label htmlFor="password">Contraseña:</label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="Ingresa tu contraseña"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className="login-button">Entrar</button>
          {error && <p className="error-message" style={{ color: 'red', marginTop: '10px' }}>{error}</p>}
        </form>
        <p className="demo-message">Esta es una pantalla de login de demostración.</p>
      </div>
    </div>
  );
};

export default LoginPage; 