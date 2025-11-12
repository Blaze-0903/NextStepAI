import { useCallback } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

const CareerVisualizer = ({ matches, onNodeClick }) => {
  // Create nodes
  const initialNodes = [
    {
      id: 'you',
      type: 'input',
      data: {
        label: (
          <div className="text-center">
            <div className="font-bold text-base" style={{ color: '#004d40' }}>You Are Here</div>
            <div className="text-xs" style={{ color: '#00695c' }}>Current Skills</div>
          </div>
        ),
      },
      position: { x: 250, y: 50 },
      style: {
        background: 'linear-gradient(135deg, #80cbc4 0%, #4db6ac 100%)',
        color: 'white',
        border: '3px solid #00897b',
        borderRadius: '12px',
        padding: '15px 20px',
        fontSize: '14px',
        fontWeight: 'bold',
        boxShadow: '0 8px 24px rgba(0, 137, 123, 0.3)',
        width: 180,
      },
    },
    ...matches.map((match, index) => ({
      id: `job-${index}`,
      type: 'default',
      data: {
        label: (
          <div className="text-center cursor-pointer" onClick={() => onNodeClick(match.title)}>
            <div className="font-bold text-sm mb-1" style={{ color: '#004d40' }}>{match.title}</div>
            <div className="text-2xl font-bold mb-1" style={{ color: '#00897b' }}>{match.match_score}%</div>
            <div className="text-xs" style={{ color: '#00695c' }}>
              ${(match.salary_range[0] / 1000).toFixed(0)}k - ${(match.salary_range[1] / 1000).toFixed(0)}k
            </div>
          </div>
        ),
      },
      position: { x: 100 + (index * 200), y: 250 },
      style: {
        background: 'white',
        border: '2px solid #b2dfdb',
        borderRadius: '12px',
        padding: '15px',
        fontSize: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        width: 160,
        cursor: 'pointer',
        transition: 'all 0.3s',
      },
    })),
  ];

  // Create edges
  const initialEdges = matches.map((match, index) => ({
    id: `you-job-${index}`,
    source: 'you',
    target: `job-${index}`,
    type: 'smoothstep',
    animated: true,
    style: { stroke: '#00897b', strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#00897b',
    },
    label: `${match.matching_skills.length} skills`,
    labelStyle: { fill: '#00695c', fontSize: 10, fontWeight: 600 },
    labelBgStyle: { fill: '#e0f2f1', fillOpacity: 0.9 },
  }));

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback((params) => setEdges((eds) => [...eds, params]), [setEdges]);

  return (
    <div data-testid="career-visualizer" style={{ width: '100%', height: '500px', background: '#fafafa', borderRadius: '12px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            if (node.id === 'you') return '#00897b';
            return '#b2dfdb';
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        <Background variant="dots" gap={12} size={1} color="#d0d0d0" />
      </ReactFlow>
    </div>
  );
};

export default CareerVisualizer;
