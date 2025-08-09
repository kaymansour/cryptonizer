
'use client'
import React from 'react';

const cryptocurrencies = [
    {
        name: 'Bitcoin',
        description: 'Bitcoin is the first decentralized digital currency, enabling peer-to-peer transactions without intermediaries.',
    },
    {
        name: 'Ethereum',
        description: 'Ethereum is a blockchain platform that supports smart contracts and decentralized applications.',
    },
    {
        name: 'Ripple',
        description: 'Ripple is a digital payment protocol that enables fast, low-cost international money transfers.',
    },
    {
        name: 'Litecoin',
        description: 'Litecoin is a peer-to-peer cryptocurrency that offers fast transaction confirmation times.',
    },
];

export default function Page() {
    return (
        <div
            style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
               
            }}
        >
            <div
                style={{
                    display: 'flex',
                    gap: '32px',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    maxWidth: 1200,
                    width: '100%',
                }}
            >
                {cryptocurrencies.map((crypto) => (
                    <div
                        key={crypto.name}
                        style={{
                            width: 320,
                            border: 'none',
                            borderRadius: 16,
                            boxShadow: '0 4px 24px rgba(0,0,0,0.08)',
                            padding: 28,
                            background: 'white',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            transition: 'transform 0.2s, box-shadow 0.2s',
                            cursor: 'pointer',
                        }}
                        onMouseOver={e => {
                            (e.currentTarget as HTMLDivElement).style.transform = 'translateY(-4px) scale(1.03)';
                            (e.currentTarget as HTMLDivElement).style.boxShadow = '0 8px 32px rgba(0,0,0,0.12)';
                        }}
                        onMouseOut={e => {
                            (e.currentTarget as HTMLDivElement).style.transform = '';
                            (e.currentTarget as HTMLDivElement).style.boxShadow = '0 4px 24px rgba(0,0,0,0.08)';
                        }}
                    >
                        <div
                            style={{
                                fontWeight: 700,
                                fontSize: 24,
                                marginBottom: 12,
                                color: '#2d3748',
                                letterSpacing: 1,
                            }}
                        >
                            {crypto.name}
                        </div>
                        <div style={{ fontSize: 16, color: '#4a5568', textAlign: 'center' }}>
                            {crypto.description}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
