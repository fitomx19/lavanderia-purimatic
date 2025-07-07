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
  const [perPage, setPerPage] = useState(10);
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
        setEmployees(employees.filter(employee => employee._id !== id));
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
    return <div>Cargando empleados...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="users-page-container">
      <Header />
      <h1>Gestión de Usuarios (Empleados)</h1>
      <button onClick={() => setShowCreateForm(!showCreateForm)} className="create-employee-button">
        {showCreateForm ? 'Cancelar' : 'Agregar Nuevo Empleado'}
      </button>

      {showCreateForm && (
        <form onSubmit={handleCreateEmployee} className="create-employee-form">
          <h2>Crear Nuevo Empleado</h2>
          <input
            type="text"
            name="username"
            placeholder="Username"
            value={newEmployee.username}
            onChange={handleInputChange}
            required
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={newEmployee.email}
            onChange={handleInputChange}
            required
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            value={newEmployee.password}
            onChange={handleInputChange}
            required
          />
          <select name="role" value={newEmployee.role} onChange={handleInputChange}>
            <option value="empleado">Empleado</option>
            <option value="admin">Admin</option>
          </select>
          <input
            type="text"
            name="store_id"
            placeholder="Store ID"
            value={newEmployee.store_id}
            onChange={handleInputChange}
            required
          />
          <button type="submit">Guardar Empleado</button>
        </form>
      )}

      {editingEmployee && (
        <div className="edit-employee-modal">
          <form onSubmit={handleUpdateEmployee} className="edit-employee-form">
            <h2>Editar Empleado</h2>
            <label>Email:</label>
            <input
              type="email"
              name="email"
              value={editFormData.email}
              onChange={handleEditFormChange}
              required
            />
            <label>Rol:</label>
            <select name="role" value={editFormData.role} onChange={handleEditFormChange}>
              <option value="empleado">Empleado</option>
              <option value="admin">Admin</option>
            </select>
            <button type="submit">Actualizar Empleado</button>
            <button type="button" onClick={() => setEditingEmployee(null)}>Cancelar</button>
          </form>
        </div>
      )}

      <table className="users-table">
        <thead>
          <tr>
            <th>Username</th>
            <th>Email</th>
            <th>Rol</th>
            <th>Activo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {employees.map((employee) => (
            <tr key={employee._id}>
              <td>{employee.username}</td>
              <td>{employee.email}</td>
              <td>{employee.role}</td>
              <td>{employee.is_active ? 'Sí' : 'No'}</td>
              <td>
                <button onClick={() => handleEditClick(employee)}>Editar</button>
                <button onClick={() => handleDeleteEmployee(employee._id)}>Eliminar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination-controls">
        <button onClick={handlePrevPage} disabled={currentPage === 1}>Anterior</button>
        <span>Página {currentPage} de {totalPages} ({totalEmployees} empleados)</span>
        <button onClick={handleNextPage} disabled={currentPage === totalPages}>Siguiente</button>
      </div>
    </div>
  );
};

export default UsersPage;