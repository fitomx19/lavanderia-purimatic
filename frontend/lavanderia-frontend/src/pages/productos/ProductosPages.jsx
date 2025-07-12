import React, { useState, useEffect } from 'react';
import Header from '../../components/layout/Header';
import { getProducts, createProduct, updateProduct, deleteProduct } from '../../services/productoService';
import './ProductosPages.css';

const ProductosPages = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [currentProduct, setCurrentProduct] = useState(null);
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    precio: '',
    stock: '',
    tipo: 'jabon', // Valor por defecto
  });

  useEffect(() => {
    fetchProducts();
  }, [currentPage]);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await getProducts(currentPage, 10);
      setProducts(response.data.products);
      setTotalPages(response.data.pagination.total_pages);
      setError(null);
    } catch (err) {
      setError(err.message || 'Error al cargar productos.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (currentProduct) {
        await updateProduct(currentProduct._id, formData);
      } else {
        await createProduct(formData);
      }
      setShowForm(false);
      setFormData({
        nombre: '',
        descripcion: '',
        precio: '',
        stock: '',
        tipo: 'jabon',
      });
      setCurrentProduct(null);
      fetchProducts();
    } catch (err) {
      setError(err.message || 'Error al guardar el producto.');
    }
  };

  const handleEdit = (product) => {
    setCurrentProduct(product);
    setFormData({
      nombre: product.nombre,
      descripcion: product.descripcion,
      precio: product.precio,
      stock: product.stock,
      tipo: product.tipo,
    });
    setShowForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Estás seguro de que quieres eliminar este producto?')) {
      try {
        await deleteProduct(id);
        fetchProducts();
      } catch (err) {
        setError(err.message || 'Error al eliminar el producto.');
      }
    }
  };

  const handlePageChange = (newPage) => {
    if (newPage > 0 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  return (
    <div className="productos-page">
      <Header />
      <div className="productos-container">
        <h1>Gestión de Productos</h1>
        <button onClick={() => { setShowForm(true); setCurrentProduct(null); setFormData({ nombre: '', descripcion: '', precio: '', stock: '', tipo: 'jabon' }); }} className="add-product-button">
          Agregar Nuevo Producto
        </button>

        {showForm && (
          <div className="product-form-modal">
            <div className="product-form-content">
              <h2>{currentProduct ? 'Editar Producto' : 'Agregar Producto'}</h2>
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Nombre:</label>
                  <input type="text" name="nombre" value={formData.nombre} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Descripción:</label>
                  <input type="text" name="descripcion" value={formData.descripcion} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Precio:</label>
                  <input type="number" name="precio" value={formData.precio} onChange={handleInputChange} step="0.01" required />
                </div>
                <div className="form-group">
                  <label>Stock:</label>
                  <input type="number" name="stock" value={formData.stock} onChange={handleInputChange} required />
                </div>
                <div className="form-group">
                  <label>Tipo:</label>
                  <select name="tipo" value={formData.tipo} onChange={handleInputChange} required>
                    <option value="jabon">Jabón</option>
                    <option value="suavizante">Suavizante</option>
                    <option value="bolsas">Bolsas</option>
                    <option value="detergente">Detergente</option>
                    <option value="blanqueador">Blanqueador</option>
                    <option value="quitamanchas">Quitamanchas</option>
                    <option value="otros">Otros</option>
                  </select>
                </div>
                <div className="form-actions">
                  <button type="submit">{currentProduct ? 'Actualizar' : 'Crear'}</button>
                  <button type="button" onClick={() => setShowForm(false)}>Cancelar</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {loading && <p>Cargando productos...</p>}
        {error && <p className="error-message">{error}</p>}

        {!loading && !error && products.length === 0 && <p>No hay productos disponibles.</p>}

        {!loading && !error && products.length > 0 && (
          <div className="products-table-container">
            <table className="products-table">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Descripción</th>
                  <th>Precio</th>
                  <th>Stock</th>
                  <th>Tipo</th>
                  <th>Estado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product._id}>
                    <td>{product.nombre}</td>
                    <td>{product.descripcion}</td>
                    <td>${parseFloat(product.precio).toFixed(2)}</td>
                    <td>{product.stock}</td>
                    <td>{product.tipo}</td>
                    <td>{product.is_active ? 'Activo' : 'Inactivo'}</td>
                    <td>
                      <button onClick={() => handleEdit(product)} className="edit-button">Editar</button>
                      <button onClick={() => handleDelete(product._id)} className="delete-button">Eliminar</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pagination-controls">
              <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage === 1}>
                Anterior
              </button>
              <span>Página {currentPage} de {totalPages}</span>
              <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage === totalPages}>
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductosPages;
