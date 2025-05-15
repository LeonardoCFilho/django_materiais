"use client"

import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import '../css/consulta.css';
import { Search, X } from '@geist-ui/icons';

interface Product {
    codigo: string;
    saldo: number;
    descricao: string;
}

export const Consulta: React.FC = () => {
    // Estados devem ser declarados corretamente:
    const [tempQuantFilter, setTempQuantFilter] = useState<string>('igual a');
    const [tempCodFilter, setTempCodFilter] = useState<string>('');
    const [tempDescFilter, setTempDescFilter] = useState<string>('');
    const [tempQuantValue1, setTempQuantValue1] = useState<string>('');
    const [tempQuantValue2, setTempQuantValue2] = useState<string>('');
    const [tempPageInput, setTempPageInput] = useState<string>('1');

    // Estados reais:
    const [quantFilter, setQuantFilter] = useState<string>('igual a');
    const [codFilter, setCodFilter] = useState<string>('');
    const [descFilter, setDescFilter] = useState<string>('');
    const [quantValue1, setQuantValue1] = useState<string>('');
    const [quantValue2, setQuantValue2] = useState<string>('');
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/materiais/';
    const itemsPerPage = 10;

    // Atualizar a construção da URL
    const buildApiUrl = () => {
        let url = `${API_URL}?page=${currentPage}&page_size=${itemsPerPage}`;

        if (codFilter) url += `&codigo=${encodeURIComponent(codFilter)}`;
        if (descFilter) url += `&descricao=${encodeURIComponent(descFilter)}`;

        if (quantValue1) {
            url += `&saldo=${quantValue1}`;
            switch (quantFilter) {
                case 'menor ou igual a': url += '&saldo_filter=menorq'; break;
                case 'maior ou igual a': url += '&saldo_filter=maiorq'; break;
                case 'igual a': url += '&saldo_filter=igual'; break;
                case 'entre':
                    url += `&saldo_filter=entre&saldo_between_end=${quantValue2}`;
                    break;
            }
        }

        return url;
    };

    // Função para buscar produtos da API
    const fetchProducts = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(buildApiUrl());
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setProducts(data.results || []);
            setTotalPages(data.total_pages || 1);
            setCurrentPage(data.current_page || 1);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro desconhecido');
        } finally {
            setLoading(false);
        }
    }, [currentPage, quantFilter, quantValue1, quantValue2, codFilter, descFilter]);

    // Debounce para a busca
    useEffect(() => {
        const debouncedFetch = debounce(fetchProducts, 500);
        debouncedFetch();
        return () => debouncedFetch.cancel();
    }, [fetchProducts]);

    // Função para aplicar filtros
    const applyFilters = () => {
        setCodFilter(tempCodFilter);
        setDescFilter(tempDescFilter);
        setQuantValue1(tempQuantValue1);
        setQuantValue2(tempQuantValue2);
        setQuantFilter(tempQuantFilter); // Atualiza o filtro real aqui

        // Aplicar a página digitada
        const page = Math.max(1, Math.min(totalPages, Number(tempPageInput) || 1));
        setCurrentPage(page);
        setTempPageInput(page.toString());
    };

    // Função para limpar filtros
    const clearFilters = () => {
        setTempQuantFilter('igual a');
        setQuantFilter('igual a');
        setTempQuantValue1('');
        setTempQuantValue2('');
        setTempCodFilter('');
        setTempDescFilter('');
        setTempPageInput('1');
        setCodFilter('');
        setDescFilter('');
        setQuantValue1('');
        setQuantValue2('');
        setCurrentPage(1);
    };

    // Função para lidar com pressionar Enter nos inputs
    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            applyFilters();
        }
    };

    return (
        <div className="consulta-container">
            {/* Container de filtros superior */}
            <div className="filter-header">
                <p id='mobile' className="instruction-text">Clique na linha para ver descrição completa</p>
                <button
                    className="filter-btn clear-btn"
                    onClick={clearFilters}
                    data-tooltip="Resetar filtros"
                    disabled={loading}
                >
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
                <button
                    className="filter-btn apply-btn"
                    onClick={applyFilters}
                    data-tooltip="Filtrar resultados"
                    disabled={loading}
                >
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
                            value={tempQuantFilter}
                            onChange={(e) => setTempQuantFilter(e.target.value)}
                            disabled={loading}
                        >
                            <option value="menor ou igual a">Menor ou igual a</option>
                            <option value="maior ou igual a">Maior ou igual a</option>
                            <option value="igual a">Igual a</option>
                            <option value="entre">Entre</option>
                        </select>

                        <input
                            type="number"
                            value={tempQuantValue1}
                            onChange={(e) => setTempQuantValue1(e.target.value)}
                            placeholder="Valor"
                            disabled={loading}
                            onKeyPress={handleKeyPress}
                        />

                        {tempQuantFilter === 'entre' && (
                            <>
                                <span className="and-text">E</span>
                                <input
                                    type="number"
                                    value={tempQuantValue2}
                                    onChange={(e) => setTempQuantValue2(e.target.value)}
                                    placeholder="Valor"
                                    disabled={loading}
                                    onKeyPress={handleKeyPress}
                                />
                            </>
                        )}
                    </div>
                </div>

                {/* Filtro de código */}
                <div className="filter-group">
                    <label id="code-filter">Filtro de código</label>
                    <div className="search-input">
                        <Search size={16} className="search-icon" onClick={applyFilters} />
                        <input
                            type="text"
                            value={tempCodFilter}
                            onChange={(e) => setTempCodFilter(e.target.value)}
                            placeholder="Pesquisar..."
                            disabled={loading}
                            onKeyPress={handleKeyPress}
                        />
                    </div>
                </div>

                {/* Filtro de descrição */}
                <div className="filter-group">
                    <label id="description-filter">Filtro de descrição</label>
                    <div className="search-input">
                        <Search size={16} className="search-icon" onClick={applyFilters} />
                        <textarea
                            value={tempDescFilter}
                            onChange={(e) => setTempDescFilter(e.target.value)}
                            placeholder="Pesquisar..."
                            rows={1}
                            disabled={loading}
                            onKeyPress={handleKeyPress}
                        />
                    </div>
                </div>
            </div>

            {/* Mensagem de erro */}
            {error && (
                <div className="error-message">
                    {error}
                    <button onClick={fetchProducts} className="retry-button">
                        Tentar novamente
                    </button>
                </div>
            )}

            {/* Tabela de resultados */}
            <div className="results-table">
                <div className="table-header">
                    <div className="col-cod">Código</div>
                    <div className="col-saldo">Saldo</div>
                    <div className="col-desc">Descrição</div>
                </div>

                {loading ? (
                    <div className="loading-container">
                        <div className="loading-spinner"></div>
                        <p>Carregando dados...</p>
                    </div>
                ) : products.length === 0 ? (
                    <div className="no-results">
                        Nenhum resultado encontrado com os filtros atuais
                    </div>
                ) : (
                    products.map((product, index) => (
                        <div
                            key={`${product.codigo}-${index}`}
                            className={`table-row ${index % 2 === 0 ? 'even' : 'odd'}`}
                            onClick={() => setSelectedProduct(product)}
                        >
                            <div className="col-cod">{product.codigo}</div>
                            <div className="col-saldo">{product.saldo}</div>
                            <div className="col-desc" title={product.descricao}>
                                {product.descricao.length > 100
                                    ? `${product.descricao.substring(0, 200)}...`
                                    : product.descricao}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Paginação */}
            {products.length > 0 && (
                <div className="pagination">
                    <button
                        onClick={() => {
                            setCurrentPage(1);
                            setTempPageInput('1');
                        }}
                        disabled={currentPage === 1 || loading}
                    >
                        &lt;&lt;
                    </button>
                    <button
                        onClick={() => {
                            const newPage = Math.max(1, currentPage - 1);
                            setCurrentPage(newPage);
                            setTempPageInput(newPage.toString());
                        }}
                        disabled={currentPage === 1 || loading}
                    >
                        &lt;
                    </button>

                    <span className="page-input">
                        Página <input
                            type="number"
                            min="1"
                            max={totalPages}
                            value={tempPageInput}
                            onChange={(e) => setTempPageInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            disabled={loading}
                        /> de {totalPages}
                    </span>

                    <button
                        onClick={() => {
                            const newPage = Math.min(totalPages, currentPage + 1);
                            setCurrentPage(newPage);
                            setTempPageInput(newPage.toString());
                        }}
                        disabled={currentPage === totalPages || loading}
                    >
                        &gt;
                    </button>
                    <button
                        onClick={() => {
                            setCurrentPage(totalPages);
                            setTempPageInput(totalPages.toString());
                        }}
                        disabled={currentPage === totalPages || loading}
                    >
                        &gt;&gt;
                    </button>
                </div>
            )}

            {/* Botão voltar */}
            <div className="footer">
                <button className="back-btn" disabled={loading}>
                    {'<<'} Voltar
                </button>
            </div>

            {/* Modal de detalhes */}
            {selectedProduct && (
                <div className="modal-overlay" onClick={() => setSelectedProduct(null)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3 id="product">Produto escolhido</h3>
                            <button
                                onClick={() => setSelectedProduct(null)}
                                aria-label="Fechar modal"
                            >
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
                                <span>{selectedProduct.codigo}</span>
                            </div>
                            <div className="modal-row full-width">
                                <span id='last'>Descrição:</span>
                                <textarea
                                    value={selectedProduct.descricao}
                                    readOnly
                                    aria-label="Descrição completa do produto"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};