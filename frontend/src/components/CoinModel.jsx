import React, { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'

function CoinModel() {
    // Reference to the mesh for rotation
    const coinRef = useRef(null)

    // Rotate the coin on each frame
    useFrame(() => {
        if (coinRef.current) {
            coinRef.current.rotation.y += 0.01
        }
    })

    return (
        <Canvas style={{ width: 200, height: 200 }} aria-label="Rotating 3D coin model">
            {/* Basic lighting for the scene */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 5, 5]} intensity={0.8} />

            {/* Coin mesh: a thin cylinder standing upright */}
            <mesh ref={coinRef} rotation={[Math.PI / 2, 0, 0.2]}>
                <cylinderGeometry args={[1, 1, 0.1, 32]} />
                <meshStandardMaterial color="#FFD700" metalness={0.9} roughness={0.2} />
            </mesh>
        </Canvas>
    )
}

export default CoinModel
