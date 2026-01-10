# Marcus Avatar - Three.js Design Document

## 1. Overview

The Marcus avatar is a stylized 3D head that communicates the AI's hidden emotional state through visual cues. This creates an engaging, game-like experience where users must "read" Marcus to negotiate effectively.

### 1.1 Design Goals

| Goal | Implementation |
|------|----------------|
| **Readable emotions** | Clear, exaggerated expressions visible at a glance |
| **Real-time responsiveness** | <16ms frame time, smooth 60fps animations |
| **Visual storytelling** | Patience/stress become tangible through effects |
| **Hackathon-friendly** | Achievable in 3-4 hours with existing assets |

### 1.2 Visual Style Options

For a hackathon, choose ONE style based on available time:

| Style | Effort | Impact | Recommendation |
|-------|--------|--------|----------------|
| **Abstract orb** | 2 hours | Medium | Safe fallback |
| **Low-poly head** | 3 hours | High | **Recommended** |
| **Stylized cartoon** | 4 hours | Very High | If skilled in Blender |
| **Realistic** | 8+ hours | Variable | Skip for hackathon |

---

## 2. Technical Architecture

### 2.1 Tech Stack

```
React Three Fiber (R3F)     - React wrapper for Three.js
@react-three/drei           - Useful helpers (useGLTF, OrbitControls, etc.)
@react-three/postprocessing - Screen effects (vignette, color grading)
three                       - Core Three.js
zustand                     - State management (bridges React ↔ Three.js)
```

### 2.2 Component Structure

```
MarcusScene
├── Canvas (R3F)
│   ├── Lighting
│   │   ├── ambientLight
│   │   ├── directionalLight (key)
│   │   └── pointLight (fill)
│   │
│   ├── MarcusHead
│   │   ├── FaceMesh
│   │   │   └── MorphTargets (expressions)
│   │   ├── Eyes
│   │   │   ├── LeftEye
│   │   │   └── RightEye
│   │   └── Mouth
│   │       └── LipSyncController
│   │
│   ├── ParticleEffects
│   │   ├── SweatDrops (stress > 60)
│   │   └── SteamPuffs (patience < 30)
│   │
│   ├── Environment
│   │   └── BackgroundGradient
│   │
│   └── EffectComposer
│       ├── Vignette (patience-based)
│       └── ColorGrading (emotion-based)
│
└── HTML Overlay (via drei's Html)
    └── StatusIndicator
```

### 2.3 State Flow

```
Server State               React State              Three.js State
────────────────           ────────────────         ────────────────
patience: 45        →      patience: 45       →     morphTargets.annoyed: 0.6
stress: 70          →      stress: 70         →     particles.sweat.intensity: 0.7
emotion: "stressed" →      emotion: "stressed"→     faceColor: warmShift
isSpeaking: true    →      isSpeaking: true   →     mouth.openAmount: audioLevel
                           audioLevel: 0.8    →
```

---

## 3. Expression System

### 3.1 Morph Targets (Blend Shapes)

The 3D model needs these morph targets for facial expressions:

```typescript
interface MorphTargets {
  // Eyebrows
  browRaiseLeft: number;      // 0-1
  browRaiseRight: number;     // 0-1
  browFurrow: number;         // 0-1

  // Eyes
  eyeSquintLeft: number;      // 0-1
  eyeSquintRight: number;     // 0-1
  eyeWideLeft: number;        // 0-1
  eyeWideRight: number;       // 0-1

  // Mouth
  mouthSmile: number;         // 0-1
  mouthFrown: number;         // 0-1
  mouthOpen: number;          // 0-1 (for lip sync)
  mouthTense: number;         // 0-1

  // Cheeks
  cheekPuff: number;          // 0-1 (for stress)
}
```

### 3.2 Expression Presets

```typescript
const EXPRESSION_PRESETS = {
  neutral: {
    browRaiseLeft: 0,
    browRaiseRight: 0,
    browFurrow: 0,
    eyeSquintLeft: 0,
    eyeSquintRight: 0,
    mouthSmile: 0.2,
    mouthFrown: 0,
    mouthTense: 0,
  },

  impressed: {
    browRaiseLeft: 0.7,
    browRaiseRight: 0.7,
    browFurrow: 0,
    eyeWideLeft: 0.3,
    eyeWideRight: 0.3,
    mouthSmile: 0.8,
    mouthFrown: 0,
    mouthTense: 0,
  },

  skeptical: {
    browRaiseLeft: 0.6,
    browRaiseRight: 0,
    browFurrow: 0.3,
    eyeSquintLeft: 0.4,
    eyeSquintRight: 0.2,
    mouthSmile: 0,
    mouthFrown: 0.2,
    mouthTense: 0.5,
  },

  stressed: {
    browRaiseLeft: 0.2,
    browRaiseRight: 0.2,
    browFurrow: 0.7,
    eyeSquintLeft: 0.3,
    eyeSquintRight: 0.3,
    mouthSmile: 0,
    mouthFrown: 0.4,
    mouthTense: 0.8,
    cheekPuff: 0.3,
  },

  annoyed: {
    browRaiseLeft: 0,
    browRaiseRight: 0,
    browFurrow: 0.9,
    eyeSquintLeft: 0.6,
    eyeSquintRight: 0.6,
    mouthSmile: 0,
    mouthFrown: 0.6,
    mouthTense: 0.7,
  },

  impatient: {
    browRaiseLeft: 0,
    browRaiseRight: 0.4,
    browFurrow: 0.5,
    eyeSquintLeft: 0.2,
    eyeSquintRight: 0.2,
    mouthSmile: 0,
    mouthFrown: 0.3,
    mouthTense: 0.4,
  },
};
```

### 3.3 Expression Blending

```typescript
// hooks/useExpressionBlend.ts
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

export function useExpressionBlend(
  mesh: THREE.Mesh,
  targetEmotion: string,
  transitionSpeed: number = 0.1
) {
  const currentValues = useRef<Record<string, number>>({});

  useFrame((_, delta) => {
    if (!mesh.morphTargetInfluences || !mesh.morphTargetDictionary) return;

    const target = EXPRESSION_PRESETS[targetEmotion] || EXPRESSION_PRESETS.neutral;

    // Lerp each morph target toward its target value
    Object.entries(target).forEach(([key, targetValue]) => {
      const index = mesh.morphTargetDictionary![key];
      if (index === undefined) return;

      const current = mesh.morphTargetInfluences![index] || 0;
      const newValue = THREE.MathUtils.lerp(current, targetValue, transitionSpeed);
      mesh.morphTargetInfluences![index] = newValue;
    });
  });
}
```

---

## 4. Lip Sync System

### 4.1 Audio Analysis

```typescript
// hooks/useLipSync.ts
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';

interface LipSyncProps {
  audioContext: AudioContext;
  analyser: AnalyserNode;
  mesh: THREE.Mesh;
  mouthMorphTarget: string;
}

export function useLipSync({ audioContext, analyser, mesh, mouthMorphTarget }: LipSyncProps) {
  const dataArray = useRef(new Uint8Array(analyser.frequencyBinCount));

  useFrame(() => {
    if (!mesh.morphTargetInfluences || !mesh.morphTargetDictionary) return;

    analyser.getByteFrequencyData(dataArray.current);

    // Get average volume from frequency data
    const average = dataArray.current.reduce((a, b) => a + b, 0) / dataArray.current.length;
    const normalized = average / 255;

    // Apply smoothing
    const mouthIndex = mesh.morphTargetDictionary[mouthMorphTarget];
    if (mouthIndex !== undefined) {
      const current = mesh.morphTargetInfluences[mouthIndex];
      mesh.morphTargetInfluences[mouthIndex] = THREE.MathUtils.lerp(
        current,
        normalized * 0.8, // Scale down a bit
        0.3 // Smooth transition
      );
    }
  });
}
```

### 4.2 Simple Lip Sync (Fallback)

If audio analysis is too complex, use a simple oscillation when `isSpeaking`:

```typescript
function SimpleLipSync({ isSpeaking, mesh }) {
  useFrame(({ clock }) => {
    if (!mesh.morphTargetInfluences) return;

    const mouthIndex = mesh.morphTargetDictionary?.mouthOpen;
    if (mouthIndex === undefined) return;

    if (isSpeaking) {
      // Oscillate mouth open/close at speech-like frequency
      const time = clock.getElapsedTime();
      const oscillation = (Math.sin(time * 10) + 1) / 2; // 0-1 at ~1.6Hz
      const variation = (Math.sin(time * 3) + 1) / 4;   // Slower variation
      mesh.morphTargetInfluences[mouthIndex] = oscillation * 0.5 + variation * 0.3;
    } else {
      // Close mouth smoothly
      mesh.morphTargetInfluences[mouthIndex] *= 0.9;
    }
  });

  return null;
}
```

---

## 5. Eye System

### 5.1 Eye Movement

```typescript
// components/three/EyeController.tsx
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

interface EyeControllerProps {
  leftEye: THREE.Object3D;
  rightEye: THREE.Object3D;
  isThinking: boolean;
  isSpeaking: boolean;
  lookAtUser: boolean;
}

export function EyeController({
  leftEye,
  rightEye,
  isThinking,
  isSpeaking,
  lookAtUser,
}: EyeControllerProps) {
  const targetRef = useRef(new THREE.Vector3(0, 0, 5));
  const currentRef = useRef(new THREE.Vector3(0, 0, 5));
  const nextBlinkTime = useRef(0);
  const isBlinking = useRef(false);

  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();

    // Determine look target
    if (isThinking) {
      // Look up and to the side when thinking
      targetRef.current.set(
        Math.sin(time * 0.5) * 2,
        1.5 + Math.sin(time * 0.3) * 0.5,
        3
      );
    } else if (isSpeaking || lookAtUser) {
      // Look at camera (user)
      targetRef.current.set(
        Math.sin(time * 0.2) * 0.3, // Subtle movement
        Math.sin(time * 0.15) * 0.2,
        5
      );
    } else {
      // Idle - slight random movement
      targetRef.current.set(
        Math.sin(time * 0.1) * 0.5,
        Math.sin(time * 0.08) * 0.3,
        5
      );
    }

    // Smooth follow
    currentRef.current.lerp(targetRef.current, 0.05);

    // Apply to eyes
    leftEye.lookAt(currentRef.current);
    rightEye.lookAt(currentRef.current);

    // Blinking
    if (time > nextBlinkTime.current && !isBlinking.current) {
      isBlinking.current = true;
      nextBlinkTime.current = time + 2 + Math.random() * 3; // 2-5 seconds between blinks
    }
  });

  return null;
}
```

### 5.2 Blink Animation

```typescript
function useBlinking(mesh: THREE.Mesh) {
  const blinkProgress = useRef(0);
  const isBlinking = useRef(false);
  const nextBlinkTime = useRef(2);

  useFrame(({ clock }, delta) => {
    const time = clock.getElapsedTime();

    // Trigger blink
    if (time > nextBlinkTime.current && !isBlinking.current) {
      isBlinking.current = true;
      blinkProgress.current = 0;
      nextBlinkTime.current = time + 2 + Math.random() * 4;
    }

    // Animate blink
    if (isBlinking.current) {
      blinkProgress.current += delta * 8; // Speed of blink

      // Blink curve: quick close, slightly slower open
      let blinkValue: number;
      if (blinkProgress.current < 0.5) {
        blinkValue = blinkProgress.current * 2; // Close
      } else if (blinkProgress.current < 1) {
        blinkValue = 2 - blinkProgress.current * 2; // Open
      } else {
        blinkValue = 0;
        isBlinking.current = false;
      }

      // Apply to both eye squint morphs
      const leftIndex = mesh.morphTargetDictionary?.eyeSquintLeft;
      const rightIndex = mesh.morphTargetDictionary?.eyeSquintRight;

      if (leftIndex !== undefined) {
        mesh.morphTargetInfluences![leftIndex] = Math.max(
          mesh.morphTargetInfluences![leftIndex],
          blinkValue
        );
      }
      if (rightIndex !== undefined) {
        mesh.morphTargetInfluences![rightIndex] = Math.max(
          mesh.morphTargetInfluences![rightIndex],
          blinkValue
        );
      }
    }
  });
}
```

---

## 6. Particle Effects

### 6.1 Sweat Drops (High Stress)

```typescript
// components/three/SweatParticles.tsx
import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';

interface SweatParticlesProps {
  stress: number; // 0-100
  headPosition: THREE.Vector3;
}

export function SweatParticles({ stress, headPosition }: SweatParticlesProps) {
  const particlesRef = useRef<THREE.Points>(null);
  const particleCount = 20;

  const { positions, velocities } = useMemo(() => {
    const positions = new Float32Array(particleCount * 3);
    const velocities = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      // Start at random position on forehead
      positions[i * 3] = (Math.random() - 0.5) * 0.3;
      positions[i * 3 + 1] = 0.8 + Math.random() * 0.2;
      positions[i * 3 + 2] = 0.3;

      // Velocity: fall down with slight randomness
      velocities[i * 3] = (Math.random() - 0.5) * 0.01;
      velocities[i * 3 + 1] = -0.02 - Math.random() * 0.02;
      velocities[i * 3 + 2] = 0;
    }

    return { positions, velocities };
  }, []);

  useFrame(() => {
    if (!particlesRef.current) return;

    const positionAttr = particlesRef.current.geometry.attributes.position;
    const posArray = positionAttr.array as Float32Array;

    // Only show particles when stress > 60
    const spawnRate = stress > 60 ? (stress - 60) / 40 : 0; // 0-1

    for (let i = 0; i < particleCount; i++) {
      // Update position
      posArray[i * 3] += velocities[i * 3];
      posArray[i * 3 + 1] += velocities[i * 3 + 1];
      posArray[i * 3 + 2] += velocities[i * 3 + 2];

      // Reset if fallen too far
      if (posArray[i * 3 + 1] < -0.5 && Math.random() < spawnRate * 0.1) {
        posArray[i * 3] = (Math.random() - 0.5) * 0.3;
        posArray[i * 3 + 1] = 0.8 + Math.random() * 0.2;
        posArray[i * 3 + 2] = 0.3;
      }
    }

    positionAttr.needsUpdate = true;
  });

  // Hide when stress is low
  if (stress < 60) return null;

  return (
    <points ref={particlesRef} position={headPosition}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particleCount}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color="#88ccff"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}
```

### 6.2 Steam Puffs (Low Patience)

```typescript
// components/three/SteamEffect.tsx
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

interface SteamEffectProps {
  patience: number; // 0-100
  position: THREE.Vector3;
}

export function SteamEffect({ patience, position }: SteamEffectProps) {
  const steamRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (!steamRef.current) return;

    const time = clock.getElapsedTime();

    // Pulsing scale
    const intensity = patience < 30 ? (30 - patience) / 30 : 0;
    const pulse = 1 + Math.sin(time * 5) * 0.2 * intensity;

    steamRef.current.scale.set(pulse, pulse, pulse);
    steamRef.current.material.opacity = intensity * 0.4;

    // Rise and fade
    steamRef.current.position.y = position.y + 1 + Math.sin(time * 2) * 0.1;
  });

  if (patience >= 30) return null;

  return (
    <mesh ref={steamRef} position={[position.x + 0.5, position.y + 1, position.z]}>
      <sphereGeometry args={[0.15, 16, 16]} />
      <meshBasicMaterial color="#ff6666" transparent opacity={0.3} />
    </mesh>
  );
}
```

---

## 7. Post-Processing Effects

### 7.1 Dynamic Vignette

```typescript
// components/three/PostProcessing.tsx
import { EffectComposer, Vignette, ChromaticAberration } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';

interface PostProcessingProps {
  patience: number;
  stress: number;
}

export function PostProcessing({ patience, stress }: PostProcessingProps) {
  // Vignette gets stronger as patience drops
  const vignetteIntensity = patience < 50
    ? (50 - patience) / 50 * 0.5  // Max 0.5
    : 0;

  // Chromatic aberration when very stressed
  const aberrationOffset = stress > 70
    ? (stress - 70) / 30 * 0.003  // Max 0.003
    : 0;

  return (
    <EffectComposer>
      <Vignette
        eskil={false}
        offset={0.1}
        darkness={vignetteIntensity}
        blendFunction={BlendFunction.NORMAL}
      />
      {aberrationOffset > 0 && (
        <ChromaticAberration
          offset={[aberrationOffset, aberrationOffset]}
          blendFunction={BlendFunction.NORMAL}
        />
      )}
    </EffectComposer>
  );
}
```

### 7.2 Color Grading by Emotion

```typescript
// Apply color shift based on emotion
const EMOTION_COLORS = {
  neutral: { hue: 0, saturation: 0, brightness: 0 },
  impressed: { hue: 0.05, saturation: 0.1, brightness: 0.05 },  // Warm
  skeptical: { hue: -0.05, saturation: -0.1, brightness: -0.05 }, // Cool
  stressed: { hue: 0.02, saturation: 0.15, brightness: -0.02 },  // Slightly red
  annoyed: { hue: -0.02, saturation: -0.05, brightness: -0.1 },  // Darker
};

// Apply via CSS filter on the canvas container (simpler than shader)
function getEmotionFilter(emotion: string): string {
  const color = EMOTION_COLORS[emotion] || EMOTION_COLORS.neutral;
  return `
    hue-rotate(${color.hue * 360}deg)
    saturate(${1 + color.saturation})
    brightness(${1 + color.brightness})
  `;
}
```

---

## 8. Complete Scene Component

```tsx
// components/three/MarcusScene.tsx
import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { OrbitControls, Environment, useGLTF } from '@react-three/drei';
import { useNegotiationStore } from '@/stores/negotiationStore';
import { MarcusHead } from './MarcusHead';
import { SweatParticles } from './SweatParticles';
import { SteamEffect } from './SteamEffect';
import { PostProcessing } from './PostProcessing';

export function MarcusScene() {
  const { patience, stress, emotion, isSpeaking, isThinking, audioLevel } =
    useNegotiationStore();

  return (
    <div
      className="marcus-canvas-container"
      style={{
        filter: getEmotionFilter(emotion),
        transition: 'filter 0.5s ease',
      }}
    >
      <Canvas
        camera={{ position: [0, 0, 3], fov: 45 }}
        dpr={[1, 2]} // Responsive DPR
      >
        <Suspense fallback={null}>
          {/* Lighting */}
          <ambientLight intensity={0.4} />
          <directionalLight
            position={[5, 5, 5]}
            intensity={0.8}
            castShadow
          />
          <pointLight position={[-5, 0, 5]} intensity={0.3} color="#ffeedd" />

          {/* Environment for reflections */}
          <Environment preset="studio" />

          {/* Marcus */}
          <MarcusHead
            emotion={emotion}
            patience={patience}
            stress={stress}
            isSpeaking={isSpeaking}
            isThinking={isThinking}
            audioLevel={audioLevel}
          />

          {/* Effects */}
          <SweatParticles stress={stress} headPosition={[0, 0, 0]} />
          <SteamEffect patience={patience} position={[0, 0, 0]} />

          {/* Post-processing */}
          <PostProcessing patience={patience} stress={stress} />
        </Suspense>
      </Canvas>
    </div>
  );
}
```

---

## 9. Fallback: Abstract Orb

If 3D head is too complex for the hackathon timeline, use an abstract orb:

```tsx
// components/three/MarcusOrb.tsx
import { useFrame } from '@react-three/fiber';
import { useRef, useMemo } from 'react';
import * as THREE from 'three';

const EMOTION_COLORS = {
  neutral: '#4488ff',
  impressed: '#44ff88',
  skeptical: '#ffaa44',
  stressed: '#ff6644',
  annoyed: '#ff4444',
};

export function MarcusOrb({ emotion, patience, stress, isSpeaking }) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Create distortion based on stress
  const geometry = useMemo(() => {
    const geo = new THREE.IcosahedronGeometry(1, 4);
    // Store original positions for distortion
    geo.userData.originalPositions = geo.attributes.position.array.slice();
    return geo;
  }, []);

  useFrame(({ clock }) => {
    if (!meshRef.current) return;

    const time = clock.getElapsedTime();

    // Pulsing based on speaking
    const speakPulse = isSpeaking ? 1 + Math.sin(time * 10) * 0.05 : 1;

    // Stress causes jitter
    const stressJitter = stress > 50 ? (stress - 50) / 500 : 0;
    const jitterX = Math.sin(time * 20) * stressJitter;
    const jitterY = Math.cos(time * 23) * stressJitter;

    // Low patience causes faster rotation
    const rotationSpeed = 0.5 + (100 - patience) / 100;

    meshRef.current.scale.setScalar(speakPulse);
    meshRef.current.position.x = jitterX;
    meshRef.current.position.y = jitterY;
    meshRef.current.rotation.y += 0.01 * rotationSpeed;

    // Morph geometry based on stress
    const positions = meshRef.current.geometry.attributes.position;
    const original = meshRef.current.geometry.userData.originalPositions;
    const stressFactor = stress / 100;

    for (let i = 0; i < positions.count; i++) {
      const ox = original[i * 3];
      const oy = original[i * 3 + 1];
      const oz = original[i * 3 + 2];

      // Add noise displacement
      const noise = Math.sin(ox * 10 + time * 2) * Math.cos(oy * 10 + time * 1.5) * stressFactor * 0.1;

      positions.array[i * 3] = ox + ox * noise;
      positions.array[i * 3 + 1] = oy + oy * noise;
      positions.array[i * 3 + 2] = oz + oz * noise;
    }
    positions.needsUpdate = true;
  });

  const color = EMOTION_COLORS[emotion] || EMOTION_COLORS.neutral;

  return (
    <mesh ref={meshRef} geometry={geometry}>
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.2}
        roughness={0.3}
        metalness={0.7}
      />
    </mesh>
  );
}
```

---

## 10. Asset Requirements

### 10.1 3D Model Specifications

If creating a custom model:

| Property | Requirement |
|----------|-------------|
| Format | GLTF/GLB |
| Polycount | <10,000 triangles |
| Texture Size | 1024x1024 max |
| Morph Targets | See Section 3.1 |
| Rigged | Optional (for head movement) |

### 10.2 Quick Asset Sources

| Source | Type | License |
|--------|------|---------|
| [Ready Player Me](https://readyplayer.me/) | Realistic avatars | Free for dev |
| [Mixamo](https://www.mixamo.com/) | Rigged characters | Free |
| [Sketchfab](https://sketchfab.com/) | Various | Check per-model |
| [Three.js Examples](https://threejs.org/examples/) | Basic shapes | MIT |

### 10.3 Hackathon Shortcut

Use Ready Player Me's half-body avatar API:
1. Create avatar at readyplayer.me
2. Export GLB with blend shapes
3. Load with `useGLTF` in R3F

This gets you a usable face with morph targets in minutes.

---

## 11. Performance Optimization

### 11.1 Frame Budget

Target: 60fps (16.67ms per frame)

| Task | Budget |
|------|--------|
| Expression lerping | <1ms |
| Lip sync | <1ms |
| Particle update | <2ms |
| Render | <10ms |
| **Total** | <14ms |

### 11.2 Optimization Tips

1. **Use `instancedMesh`** for particles
2. **Limit morph targets** to those actively used
3. **Disable shadows** if not critical
4. **Use lower DPR** on mobile: `dpr={[1, 1.5]}`
5. **Memoize geometries and materials**
6. **Use `useFrame` sparingly** - batch updates

### 11.3 Mobile Considerations

```tsx
// Detect mobile and reduce quality
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

<Canvas
  dpr={isMobile ? [1, 1] : [1, 2]}
  frameloop={isMobile ? 'demand' : 'always'}
>
  {/* Disable post-processing on mobile */}
  {!isMobile && <PostProcessing {...props} />}
</Canvas>
```

---

## 12. Implementation Timeline

For a hackathon, allocate 3-4 hours total:

| Task | Time | Priority |
|------|------|----------|
| Basic scene + lighting | 30 min | P0 |
| Load/display head model | 30 min | P0 |
| Expression blending | 45 min | P0 |
| Lip sync (simple) | 30 min | P1 |
| Particle effects | 30 min | P2 |
| Post-processing | 20 min | P2 |
| Polish + debugging | 30 min | P0 |

**P0 = Must have, P1 = Should have, P2 = Nice to have**

If behind schedule:
- Skip particles → use color shift instead
- Skip post-processing → rely on CSS filters
- Skip eye tracking → static eyes
