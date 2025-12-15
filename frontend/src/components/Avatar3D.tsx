import { useRef, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Environment } from '@react-three/drei'
import * as THREE from 'three'

interface VisemeData {
  start: number
  end: number
  value: string
  blendShape: string
}

interface Avatar3DProps {
  visemeData?: VisemeData[]
  emotion?: string
  isSpeaking: boolean
}

// Simple animated avatar placeholder
function AvatarModel({ emotion, isSpeaking }: { emotion: string; isSpeaking: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)

  // Get color based on emotion
  const getEmotionColor = (emotion: string) => {
    const colors: Record<string, string> = {
      joy: '#4CAF50',
      anger: '#f44336',
      sadness: '#2196F3',
      fear: '#9C27B0',
      surprise: '#FF9800',
      neutral: '#607D8B',
    }
    return colors[emotion] || colors.neutral
  }

  // Animate the avatar
  useFrame((state) => {
    if (meshRef.current) {
      // Idle animation
      meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1

      // Speaking animation - scale pulse
      if (isSpeaking) {
        const scale = 1 + Math.sin(state.clock.elapsedTime * 10) * 0.02
        meshRef.current.scale.setScalar(scale)
      } else {
        meshRef.current.scale.setScalar(1)
      }
    }
  })

  return (
    <group>
      {/* Head */}
      <mesh
        ref={meshRef}
        position={[0, 1.5, 0]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshStandardMaterial
          color={hovered ? '#FF6B35' : getEmotionColor(emotion)}
          metalness={0.3}
          roughness={0.7}
        />
      </mesh>

      {/* Eyes */}
      <mesh position={[-0.15, 1.6, 0.4]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial color="white" />
      </mesh>
      <mesh position={[0.15, 1.6, 0.4]}>
        <sphereGeometry args={[0.08, 16, 16]} />
        <meshStandardMaterial color="white" />
      </mesh>

      {/* Pupils */}
      <mesh position={[-0.15, 1.6, 0.47]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#1B3139" />
      </mesh>
      <mesh position={[0.15, 1.6, 0.47]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#1B3139" />
      </mesh>

      {/* Mouth - animated when speaking */}
      <mesh position={[0, 1.35, 0.4]}>
        <boxGeometry args={[0.2, isSpeaking ? 0.15 : 0.05, 0.05]} />
        <meshStandardMaterial color="#1B3139" />
      </mesh>

      {/* Body */}
      <mesh position={[0, 0.5, 0]}>
        <cylinderGeometry args={[0.3, 0.4, 1.2, 32]} />
        <meshStandardMaterial
          color="#FF3621"
          metalness={0.2}
          roughness={0.8}
        />
      </mesh>

      {/* Arms */}
      <mesh position={[-0.5, 0.6, 0]} rotation={[0, 0, Math.PI / 6]}>
        <capsuleGeometry args={[0.08, 0.5, 8, 16]} />
        <meshStandardMaterial color="#FF6B35" />
      </mesh>
      <mesh position={[0.5, 0.6, 0]} rotation={[0, 0, -Math.PI / 6]}>
        <capsuleGeometry args={[0.08, 0.5, 8, 16]} />
        <meshStandardMaterial color="#FF6B35" />
      </mesh>

      {/* Platform */}
      <mesh position={[0, -0.2, 0]} receiveShadow>
        <cylinderGeometry args={[0.8, 0.8, 0.1, 32]} />
        <meshStandardMaterial color="#2D4550" />
      </mesh>
    </group>
  )
}

export function Avatar3D({ visemeData: _visemeData, emotion = 'neutral', isSpeaking }: Avatar3DProps) {
  // Note: visemeData will be used for advanced lip sync in future
  void _visemeData
  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: [0, 1.5, 3], fov: 50 }}
        shadows
      >
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[5, 10, 5]}
          intensity={1}
          castShadow
        />
        <pointLight position={[-5, 5, 5]} intensity={0.3} />

        <AvatarModel emotion={emotion} isSpeaking={isSpeaking} />

        <OrbitControls
          enablePan={false}
          minDistance={2}
          maxDistance={5}
          target={[0, 1.2, 0]}
        />

        <Environment preset="studio" />
      </Canvas>
    </div>
  )
}
