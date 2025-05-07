"use client"

import React, { useState } from 'react';
import '../css/consulta.css';
import { Search, X } from '@geist-ui/icons';

export const Consulta: React.FC = () => {
    // Estados para os filtros
    const [quantFilter, setQuantFilter] = useState('igual a');
    const [quantValue1, setQuantValue1] = useState('');
    const [quantValue2, setQuantValue2] = useState('');
    const [codFilter, setCodFilter] = useState('');
    const [descFilter, setDescFilter] = useState('');
    const [selectedProduct, setSelectedProduct] = useState<any>(null);
    const [currentPage, setCurrentPage] = useState(1);

    // Dados mockados - substitua pelos seus dados reais
    const products = Array.from({ length: 50 }, (_, i) => ({
        cod: `COD${1000 + i}`,
        saldo: Math.floor(Math.random() * 100),
        descricao: `Descrição extensa do produto ${i + 1} que pode ocupar várias linhas e aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa. `.repeat(3)
    }));

    // Paginação
    const itemsPerPage = 7;
    const totalPages = Math.ceil(products.length / itemsPerPage);
    const paginatedProducts = products.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    // Função para aplicar filtros
    const applyFilters = () => {
        // Implemente sua lógica de filtragem aqui
        setCurrentPage(1); // Resetar para a primeira página
    };

    // Função para limpar filtros
    const clearFilters = () => {
        setQuantFilter('igual a');
        setQuantValue1('');
        setQuantValue2('');
        setCodFilter('');
        setDescFilter('');
    };

    return (
        <div className="consulta-container">
            {/* Container de filtros superior */}
            <div className="filter-header">
                <p id='mobile' className="instruction-text">Clique na linha para ver descrição completa</p>
                <button className="filter-btn clear-btn" onClick={clearFilters} data-tooltip="Resetar filtros">
                    <div className="button-wrapper">
                        <div className="text">Limpar filtros</div>
                        <span className="icon">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M13.013 3H2l8 9.46V19l4 2v-8.54l.9-1.055" />
                                <path d="m22 3-5 5" />
                                <path d="m17 3 5 5" />
                            </svg>
                        </span>
                    </div>
                </button>
                <p className="instruction-text">Clique na linha para ver descrição completa</p>
                <button className="filter-btn apply-btn" onClick={applyFilters} data-tooltip="Filtrar resultados">
                    <div className="button-wrapper">
                        <div className="text">Aplicar filtro</div>
                        <span className="icon">
                            <svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" width="24" height="24" preserveAspectRatio="xMidYMid meet" viewBox="0 0 24 24">
                                <path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" />
                            </svg>
                        </span>
                    </div>
                </button>
            </div>

            {/* Container de filtros principais */}
            <div className="main-filters">
                {/* Filtro de quantidade */}
                <div className="filter-group">
                    <label>Filtro de quantidade</label>
                    <div className="quantity-filter">
                        <select
                            value={quantFilter}
                            onChange={(e) => setQuantFilter(e.target.value)}
                        >
                            <option value="menor ou igual a">Menor ou igual a</option>
                            <option value="maior ou igual a">Maior ou igual a</option>
                            <option value="igual a">Igual a</option>
                            <option value="entre">Entre</option>
                        </select>

                        <input
                            type="number"
                            value={quantValue1}
                            onChange={(e) => setQuantValue1(e.target.value)}
                            placeholder="Valor"
                        />

                        {quantFilter === 'entre' && (
                            <>
                                <span className="and-text">E</span>
                                <input
                                    type="number"
                                    value={quantValue2}
                                    onChange={(e) => setQuantValue2(e.target.value)}
                                    placeholder="Valor"
                                />
                            </>
                        )}
                    </div>
                </div>

                {/* Filtro de código */}
                <div className="filter-group">
                    <label id="code-filter">Filtro de código</label>
                    <div className="search-input">
                        <Search size={16} className="search-icon" />
                        <input
                            type="text"
                            value={codFilter}
                            onChange={(e) => setCodFilter(e.target.value)}
                            placeholder="Pesquisar..."
                        />
                    </div>
                </div>

                {/* Filtro de descrição */}
                <div className="filter-group">
                    <label id="description-filter">Filtro de descrição</label>
                    <div className="search-input">
                        <Search size={16} className="search-icon" />
                        <textarea
                            value={descFilter}
                            onChange={(e) => setDescFilter(e.target.value)}
                            placeholder="Pesquisar..."
                            rows={1}
                        />
                    </div>
                </div>
            </div>

            {/* Tabela de resultados */}
            <div className="results-table">
                <div className="table-header">
                    <div className="col-cod">Código</div>
                    <div className="col-saldo">Saldo</div>
                    <div className="col-desc">Descrição</div>
                </div>

                {paginatedProducts.map((product, index) => (
                    <div
                        key={product.cod}
                        className={`table-row ${index % 2 === 0 ? 'even' : 'odd'}`}
                        onClick={() => setSelectedProduct(product)}
                    >
                        <div className="col-cod">{product.cod}</div>
                        <div className="col-saldo">{product.saldo}</div>
                        <div className="col-desc" title={product.descricao}>
                            {product.descricao.length > 100
                                ? `${product.descricao.substring(0, 200)}...`
                                : product.descricao}
                        </div>
                    </div>
                ))}
            </div>

            {/* Paginação */}
            <div className="pagination">
                <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1}>
                    &lt;&lt;
                </button>
                <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}>
                    &lt;
                </button>

                <span className="page-input">
                    Página <input
                        type="number"
                        min="1"
                        max={totalPages}
                        value={currentPage}
                        onChange={(e) => {
                            const page = Math.max(1, Math.min(totalPages, Number(e.target.value)));
                            setCurrentPage(page);
                        }}
                    /> de {totalPages}
                </span>

                <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}>
                    &gt;
                </button>
                <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages}>
                    &gt;&gt;
                </button>
            </div>

            {/* Botão voltar */}
            <div className="footer">
                <button className="back-btn"> {'<<'} Voltar</button>
            </div>

            {/* Modal de detalhes */}
            {selectedProduct && (
                <div className="modal-overlay">
                    <div className="modal">
                        <div className="modal-header">
                            <h3 id="product">Produto escolhido</h3>
                            <button onClick={() => setSelectedProduct(null)}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="modal-divider"></div>
                        <div className="modal-content">
                            <div className="modal-row">
                                <span>Saldo:</span>
                                <span>{selectedProduct.saldo}</span>
                            </div>
                            <div id="white" className="modal-row">
                                <span>Código:</span>
                                <span>{selectedProduct.cod}</span>
                            </div>
                            <div className="modal-row full-width">
                                <span id='last'>Descrição:</span>
                                <textarea
                                    value={selectedProduct.descricao}
                                    readOnly

                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};