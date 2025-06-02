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
    // Estados temporários
    const [tempQuantFilter, setTempQuantFilter] = useState<string>('igual a');
    const [tempCodFilter, setTempCodFilter] = useState<string>('');
    const [tempDescFilter, setTempDescFilter] = useState<string>('');
    const [tempQuantValue1, setTempQuantValue1] = useState<string>('');
    const [tempQuantValue2, setTempQuantValue2] = useState<string>('');
    const [tempPageInput, setTempPageInput] = useState<string>('1');
    const [tempUsoFilter, setTempUsoFilter] = useState<string>('uso');

    // Estados reais
    const [quantFilter, setQuantFilter] = useState<string>('igual a');
    const [codFilter, setCodFilter] = useState<string>('');
    const [descFilter, setDescFilter] = useState<string>('');
    const [quantValue1, setQuantValue1] = useState<string>('');
    const [quantValue2, setQuantValue2] = useState<string>('');
    const [usoFilter, setUsoFilter] = useState<string>('uso');
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const [totalPages, setTotalPages] = useState<number>(1);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/materiais/';
    const itemsPerPage = 10;
    const [validationError, setValidationError] = useState<string | null>(null);
    const [copiedCode, setCopiedCode] = useState<string | null>(null);

    // Função para construir parâmetros de consulta ALINHADOS COM O BACKEND
    const buildQueryParams = (): URLSearchParams => {
        const params = new URLSearchParams();
        
        // Paginação
        params.append('page', currentPage.toString());
        params.append('page_size', itemsPerPage.toString());
        
        // Filtros
        if (codFilter) params.append('codigo', codFilter);
        if (descFilter) params.append('descricao', descFilter);
        
        // Filtro de uso/desuso - VALORES EXATOS QUE O BACKEND ESPERA
        if (usoFilter === 'uso' || usoFilter === 'desuso' || usoFilter === 'uso+desuso') {
            params.append('usoDesuso', usoFilter);
        }
        
        // Filtro de saldo - ALINHADO COM O BACKEND
        if (quantValue1) {
            params.append('saldo', quantValue1);
            
            // Mapeamento de operadores para os valores que o backend espera
            const operatorMap: Record<string, string> = {
                'menor ou igual a': 'menorq',
                'maior ou igual a': 'maiorq',
                'igual a': 'igual',
                'entre': 'entre'
            };
            
            if (operatorMap[quantFilter]) {
                params.append('saldo_filter', operatorMap[quantFilter]);
                
                if (quantFilter === 'entre' && quantValue2) {
                    params.append('saldo_between_end', quantValue2);
                }
            }
        }
        
        // Ordenação - VALORES PADRÃO DO BACKEND
        params.append('campoOrdenacao', 'descricao');
        params.append('ordemOrdenacao', 'c');
        
        return params;
    };

    // Função para buscar produtos da API
    const fetchProducts = useCallback(async () => {
        setLoading(true);
        setError(null);
        
        try {
            const queryParams = buildQueryParams();
            const url = `${API_URL}?${queryParams.toString()}`;
            
            console.log("URL da API:", url); // Para depuração
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Erro ao carregar banco de dados`);
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
    }, [currentPage, codFilter, descFilter, usoFilter, quantFilter, quantValue1, quantValue2]);

    // Debounce para a busca
    useEffect(() => {
        const debouncedFetch = debounce(fetchProducts, 500);
        debouncedFetch();
        return () => debouncedFetch.cancel();
    }, [fetchProducts]);

    // Função para aplicar filtros
    const applyFilters = () => {
        // Validação do código
        if (tempCodFilter && !tempCodFilter.startsWith('30')) {
                setValidationError('⚠️ O código de materiais deve começar com 30');
                setError(null); // Limpa erros anteriores da API
                return; // Impede a requisição à API
            }
            
            setValidationError(null); // Limpa erros de validação
            setError(null); // Limpa erros da API

            setCodFilter(tempCodFilter);
            setDescFilter(tempDescFilter);
            setQuantValue1(tempQuantValue1);
            setQuantValue2(tempQuantValue2);
            setQuantFilter(tempQuantFilter);
            setUsoFilter(tempUsoFilter);
            
            // Primeiro aplica os filtros, depois ajusta a página
            const newPage = Math.max(1, Math.min(totalPages, Number(tempPageInput) || 1));
            
            // Se a página atual for maior que o novo total de páginas, vamos para a última página
            const adjustedPage = Math.min(newPage, totalPages);
            
            setCurrentPage(adjustedPage);
            setTempPageInput(adjustedPage.toString());
    };
    
    const copyToClipboard = (text: string) => {
    // Verifica se estamos no navegador antes de acessar o clipboard
        if (typeof window !== 'undefined' && navigator.clipboard) {
            navigator.clipboard.writeText(text)
                .then(() => {
                    setCopiedCode(text);
                    setTimeout(() => setCopiedCode(null), 1000);
                })
                .catch(err => {
                    console.error('Falha ao copiar:', err);
                });
        }
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
        setTempUsoFilter('uso');
        
        setCodFilter('');
        setDescFilter('');
        setQuantValue1('');
        setQuantValue2('');
        setUsoFilter('uso');
        setCurrentPage(1);
    };
    // Função para lidar com pressionar Enter nos inputs
    // Para inputs normais (código, quantidade, etc)
    const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            applyFilters();
        }
    };

    // Específica para textarea (descrição)
    const handleTextareaKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Shift+Enter - permite quebra de linha
        if (e.shiftKey && e.key === 'Enter') {
            return; // Permite o comportamento padrão (nova linha)
        }
        
        // Apenas Enter - aplica filtros e previne quebra de linha
        if (e.key === 'Enter') {
            e.preventDefault();
            applyFilters();
        }
    };

    useEffect(() => {
        setTempPageInput(currentPage.toString());
    }, [currentPage]);

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

                {/* Filtro de uso e desuso */}
                <div className="filter-group">
                    <label>Filtro de uso</label>
                    <div className="quantity-filter">
                        <select
                            value={tempUsoFilter}
                            onChange={(e) => setTempUsoFilter(e.target.value)}
                            disabled={loading}
                        >
                            <option value="uso">Materiais em uso</option>
                            <option value="desuso">Materiais em desuso</option>
                            <option value="uso+desuso">Materiais em uso e desuso</option>
                        </select>
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
                        onKeyDown={handleTextareaKeyPress}  // Usamos onKeyDown para melhor controle
                        style={{ 
                            resize: 'none', 
                            minHeight: '38px',
                            whiteSpace: 'pre-wrap' // Mantém as quebras de linha quando existirem
                        }}
                        onInput={(e) => {
                            // Auto-ajuste de altura
                            const target = e.target as HTMLTextAreaElement;
                            target.style.height = 'auto';
                            target.style.height = target.scrollHeight + 'px';
                        }}
                    />
                    </div>
                </div>
            </div>

            {/* Mensagens de erro */}
            {validationError && (
                <div className="error-message">
                    {validationError}
                </div>
            )}

            {error && !validationError && (
                <div className="error-message">
                    {error}
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
                        >
                            <div 
                                className="col-cod" 
                                onClick={() => copyToClipboard(product.codigo)}
                                style={{
                                    cursor: 'pointer',
                                    position: 'relative',
                                }}
                                title={copiedCode === product.codigo ? 'Código copiado!' : 'Clique para copiar o código'}
                            >
                                {product.codigo}
                                {copiedCode === product.codigo && (
                                    <span style={{
                                        position: 'absolute',
                                        right: '5px',
                                        color: 'green',
                                        fontSize: '0.8em'
                                    }}>✓</span>
                                )}
                            </div>
                            
                            <div 
                                className="col-saldo"
                                onClick={() => setSelectedProduct(product)}
                                style={{ cursor: 'pointer' }}
                            >
                                {product.saldo}
                            </div>
                            
                            <div 
                                className="col-desc" 
                                onClick={() => setSelectedProduct(product)}
                                title={product.descricao}
                                style={{ cursor: 'pointer' }}
                            >
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
                        onChange={(e) => {
                            const value = e.target.value;
                            // Permite apenas números ou string vazia
                            if (value === '' || /^[0-9\b]+$/.test(value)) {
                                const numValue = value === '' ? 1 : parseInt(value, 10);
                                // Garante que o valor não exceda o total de páginas
                                const clampedValue = Math.min(Math.max(1, numValue), totalPages);
                                setTempPageInput(clampedValue.toString());
                            }
                        }}
                        onBlur={() => {
                            // Quando perde o foco, corrige qualquer valor inválido
                            const page = Math.max(1, Math.min(totalPages, Number(tempPageInput) || 1));
                            setTempPageInput(page.toString());
                            if (page !== currentPage) {
                                setCurrentPage(page);
                            }
                        }}
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