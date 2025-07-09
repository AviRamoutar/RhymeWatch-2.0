import React from 'react';

const Header = () => {
    return (
        <header className="app-header" style={{ display: 'flex', alignItems: 'center', padding: '1rem' }}>
            {/* Placeholder logo */}
            <span role="img" aria-label="coin logo" style={{ fontSize: '1.5rem', marginRight: '0.5rem' }}>🪙</span>
            <h1 style={{ margin: 0 }}>RhymeWatch</h1>
        </header>
    );
};

export default Header;
