import React, { useEffect, useState } from 'react';
import { getEmployees, deleteEmployee, createEmployee, updateEmployee } from '../../services/employeeService';
import Header from '../../components/layout/Header';
import './UsersPage.css';

const UsersPage = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newEmployee, setNewEmployee] = useState({
    username: '',
    email: '',
    password: '',
    role: 'empleado',
    store_id: 'store_001',
  });
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [editFormData, setEditFormData] = useState({
    email: '',
    role: '',
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [totalEmployees, setTotalEmployees] = useState(0);

  const fetchEmployees = async () => {
    try {
      const data = await getEmployees(currentPage, perPage);
      setEmployees(data.data);
      setTotalPages(data.pagination.total_pages);
      setTotalEmployees(data.pagination.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [currentPage, perPage]);

  const handleDeleteEmployee = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este empleado?')) {
      try {
        await deleteEmployee(id);
        setEmployees(employees.filter((employee) => employee._id !== id));
        alert('Empleado eliminado exitosamente.');
      } catch (err) {
        setError(err.message);
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewEmployee({ ...newEmployee, [name]: value });
  };

  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    try {
      await createEmployee(newEmployee);
      alert('Empleado creado exitosamente.');
      setNewEmployee({
        username: '',
        email: '',
        password: '',
        role: 'empleado',
        store_id: 'store_001',
      });
      setShowCreateForm(false);
      fetchEmployees();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditClick = (employee) => {
    setEditingEmployee(employee);
    setEditFormData({ email: employee.email, role: employee.role });
  };

  const handleEditFormChange = (e) => {
    const { name, value } = e.target;
    setEditFormData({ ...editFormData, [name]: value });
  };

  const handleUpdateEmployee = async (e) => {
    e.preventDefault();
    try {
      await updateEmployee(editingEmployee._id, editFormData);
      alert('Empleado actualizado exitosamente.');
      setEditingEmployee(null);
      fetchEmployees();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  if (loading) {
    return (
      <div className="users-layout">
        <Header />
        <main className="users-content">
          <p className="users-muted">Cargando usuarios…</p>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="users-layout">
        <Header />
        <main className="users-content">
          <div className="users-msg err">Error: {error}</div>
        </main>
      </div>
    );
  }

  return (
    <div className="users-layout">
      <Header />
      <main className="users-content">
        <header className="users-page-head">
          <div>
            <h1>Administración de usuarios</h1>
            <p className="users-help">
              Alta y edición de empleados y administradores con acceso al sistema.
            </p>
          </div>
          <button
            type="button"
            className="users-btn users-btn--primary"
            onClick={() => setShowCreateForm(!showCreateForm)}
          >
            {showCreateForm ? 'Cancelar' : 'Nuevo usuario'}
          </button>
        </header>

        {showCreateForm && (
          <section className="users-card">
            <h2>Nuevo usuario</h2>
            <form onSubmit={handleCreateEmployee} className="users-form">
              <label>
                Usuario
                <input
                  type="text"
                  name="username"
                  placeholder="nombre.usuario"
                  value={newEmployee.username}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <label>
                Email
                <input
                  type="email"
                  name="email"
                  placeholder="correo@ejemplo.com"
                  value={newEmployee.email}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <label>
                Contraseña
                <input
                  type="password"
                  name="password"
                  placeholder="Contraseña"
                  value={newEmployee.password}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <label>
                Rol
                <select name="role" value={newEmployee.role} onChange={handleInputChange}>
                  <option value="empleado">Empleado</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <label>
                ID de tienda
                <input
                  type="text"
                  name="store_id"
                  placeholder="store_001"
                  value={newEmployee.store_id}
                  onChange={handleInputChange}
                  required
                />
              </label>
              <div className="users-form-actions">
                <button type="submit" className="users-btn users-btn--primary">
                  Guardar usuario
                </button>
                <button
                  type="button"
                  className="users-btn users-btn--ghost"
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </section>
        )}

        <section className="users-card">
          <div className="users-card-head">
            <h2>Usuarios</h2>
            <span className="users-count">{totalEmployees} registrados</span>
          </div>

          <div className="users-table-wrap">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Usuario</th>
                  <th>Email</th>
                  <th>Rol</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((employee) => (
                  <tr key={employee._id}>
                    <td>
                      <strong className="users-name">{employee.username}</strong>
                    </td>
                    <td>{employee.email}</td>
                    <td>
                      <span
                        className={`users-role ${
                          employee.role === 'admin' ? 'is-admin' : 'is-employee'
                        }`}
                      >
                        {employee.role === 'admin' ? 'Admin' : 'Empleado'}
                      </span>
                    </td>
                    <td>
                      <span
                        className={`users-badge ${
                          employee.is_active ? 'is-active' : 'is-inactive'
                        }`}
                      >
                        {employee.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td>
                      <div className="users-row-actions">
                        <button
                          type="button"
                          className="users-btn users-btn--sm users-btn--secondary"
                          onClick={() => handleEditClick(employee)}
                        >
                          Editar
                        </button>
                        <button
                          type="button"
                          className="users-btn users-btn--sm users-btn--danger"
                          onClick={() => handleDeleteEmployee(employee._id)}
                        >
                          Eliminar
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="users-pagination">
            <button
              type="button"
              className="users-btn users-btn--ghost"
              onClick={handlePrevPage}
              disabled={currentPage === 1}
            >
              Anterior
            </button>
            <span>
              Página {currentPage} de {totalPages}
            </span>
            <button
              type="button"
              className="users-btn users-btn--ghost"
              onClick={handleNextPage}
              disabled={currentPage === totalPages}
            >
              Siguiente
            </button>
          </div>
        </section>
      </main>

      {editingEmployee && (
        <div className="users-modal-overlay" role="dialog" aria-modal="true">
          <div className="users-modal">
            <div className="users-modal-head">
              <h2>Editar usuario · {editingEmployee.username}</h2>
              <button
                type="button"
                className="users-modal-close"
                onClick={() => setEditingEmployee(null)}
                aria-label="Cerrar"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleUpdateEmployee} className="users-form">
              <label>
                Email
                <input
                  type="email"
                  name="email"
                  value={editFormData.email}
                  onChange={handleEditFormChange}
                  required
                />
              </label>
              <label>
                Rol
                <select
                  name="role"
                  value={editFormData.role}
                  onChange={handleEditFormChange}
                >
                  <option value="empleado">Empleado</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <div className="users-form-actions">
                <button type="submit" className="users-btn users-btn--primary">
                  Guardar cambios
                </button>
                <button
                  type="button"
                  className="users-btn users-btn--ghost"
                  onClick={() => setEditingEmployee(null)}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UsersPage;
