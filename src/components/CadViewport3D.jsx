import React, { useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Center, Stage } from '@react-three/drei';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';

const GeometryModel = ({ geometry }) => {
    return (
        <mesh geometry={geometry} castShadow receiveShadow>
            <meshStandardMaterial color="#06b6d4" roughness={0.3} metalness={0.8} />
        </mesh>
    );
};

const LoadingCube = () => {
    const meshRef = React.useRef();
    useFrame((state, delta) => {
        if (!meshRef.current) return;
        meshRef.current.rotation.x += delta;
        meshRef.current.rotation.y += delta;
    });
    return (
        <mesh ref={meshRef}>
            <boxGeometry args={[10, 10, 10]} />
            <meshStandardMaterial wireframe color="cyan" transparent opacity={0.5} />
        </mesh>
    );
};

const decodeGeometry = (data) => {
    if (!data || data.format !== 'stl' || !data.data) return null;
    try {
        const byteCharacters = atob(data.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const loader = new STLLoader();
        const geom = loader.parse(byteArray.buffer);
        geom.center();
        return geom;
    } catch (e) {
        console.error('Failed to decode/parse STL:', e);
        return null;
    }
};

export default function CadViewport3D({ data, isIterating }) {
    const geometry = useMemo(() => decodeGeometry(data), [data]);

    return (
        <Canvas shadows camera={{ position: [4, 4, 4], fov: 45 }}>
            <color attach="background" args={['#101010']} />
            <Stage environment="city" intensity={0.5}>
                {data?.format === 'loading' ? (
                    <LoadingCube />
                ) : (
                    geometry && (
                        <Center>
                            <GeometryModel geometry={geometry} />
                        </Center>
                    )
                )}
            </Stage>
            <OrbitControls autoRotate={!isIterating} autoRotateSpeed={1} makeDefault />
        </Canvas>
    );
}
