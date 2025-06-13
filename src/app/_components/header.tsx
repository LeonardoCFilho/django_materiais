"use client"

import React from 'react';
import '../css/header.css';
import Link from 'next/link';
import { LogOut } from '@geist-ui/icons';

export const Header: React.FC = () => {
    // Simulando dados do usuário (substitua pelos seus dados reais)
    const userName = "Nome Completo do Usuário";

    return (
        <header className="header">
            <div className="header-container">
                <div className="logo-container">
                    Requisição Fácil
                </div>

                {/* <div className="user-section">
                    <div className="user-info">
                        <span className="user-name">{userName}</span>
                    </div>
                    <button className="logout-button">
                        <LogOut size={20} className="logout-icon" />
                    </button>
                </div> */}
            </div>
            <div className="divider"></div>
        </header>
    );
};