"use client"

import React, { useState } from 'react';
import '../css/navmenu.css';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export const NavMenu: React.FC = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const pathname = usePathname();

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);
    const closeMenu = () => setIsMenuOpen(false);

    const handleNavigation = (section: string) => {
        closeMenu();

        // Se estivermos na página inicial
        if (pathname === '/') {
            const element = document.getElementById(section);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth' });
            }
        }
        // Se estivermos em outra página
        else {
            window.location.href = `/#${section}`;
        }
    };

    return (
        <header className="header1">
            <div className="header-container1">
                {/* <Link href="/" className="logo1" onClick={closeMenu}>
                    <img src="/home-baner.png" alt="Logo" />Residência em TI
                </Link> */}

                <button
                    className={`menu-toggle ${isMenuOpen ? 'active' : ''}`}
                    aria-label="Abrir menu"
                    onClick={toggleMenu}
                >
                    <span className="hamburger"></span>
                </button>

                <nav className={`nav ${isMenuOpen ? 'active' : ''}`}>
                    <ul className="nav-list">
                        <li>
                            <Link
                                href="/"
                                onClick={(e) => {
                                    e.preventDefault();
                                    if (pathname === '/') {
                                        window.scrollTo({ top: 0, behavior: 'smooth' });
                                    } else {
                                        window.location.href = '/';
                                    }
                                    closeMenu();
                                }}
                            >
                                Início
                            </Link>
                        </li>
                        <li>
                            <Link href="/validade" onClick={closeMenu}>
                                Materiais com data de vencimento
                            </Link>
                        </li>
                    </ul>
                </nav>
            </div>
        </header>
    );
};