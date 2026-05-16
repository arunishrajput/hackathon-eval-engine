'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { evaluationApi } from '@/lib/api';
import type { Evaluation, EvaluationStage } from '@/lib/types';

export interface EvaluationStageInfo {
  id: EvaluationStage;
  label: string;
  status: 'waiting' | 'active' | 'done' | 'error';
  message?: string;
}

const STAGE_ORDER: EvaluationStage[] = [
  'pending',
  'cloning',
  'analyzing',
  'evaluating',
  'completed',
];

const STAGE_LABELS: Record<EvaluationStage, string> = {
  pending: 'Queued',
  cloning: 'Cloning Repository',
  analyzing: 'Analyzing Code',
  evaluating: 'Evaluating with AI Agents',
  completed: 'Complete',
  failed: 'Failed',
};

const STAGE_PROGRESS: Record<EvaluationStage, number> = {
  pending: 5,
  cloning: 25,
  analyzing: 50,
  evaluating: 80,
  completed: 100,
  failed: 100,
};

function buildStages(
  currentStatus: EvaluationStage,
  message?: string
): EvaluationStageInfo[] {
  const isFailed = currentStatus === 'failed';
  const currentIdx = STAGE_ORDER.indexOf(currentStatus);

  return STAGE_ORDER.map((stage, idx) => {
    let status: EvaluationStageInfo['status'];
    if (isFailed && idx === currentIdx) {
      status = 'error';
    } else if (idx < currentIdx || currentStatus === 'completed') {
      status = 'done';
    } else if (idx === currentIdx) {
      status = 'active';
    } else {
      status = 'waiting';
    }

    return {
      id: stage,
      label: STAGE_LABELS[stage],
      status,
      message: idx === currentIdx ? message : undefined,
    };
  });
}

interface UseEvaluationStreamResult {
  stages: EvaluationStageInfo[];
  currentStage: EvaluationStage;
  progress: number;
  isComplete: boolean;
  isFailed: boolean;
  error: string | null;
  agentCount: number;
}

export function useEvaluationStream(
  submissionId: string,
  onComplete: (evaluation: Evaluation) => void
): UseEvaluationStreamResult {
  const [currentStage, setCurrentStage] = useState<EvaluationStage>('pending');
  const [stages, setStages] = useState<EvaluationStageInfo[]>(() =>
    buildStages('pending')
  );
  const [progress, setProgress] = useState(5);
  const [isComplete, setIsComplete] = useState(false);
  const [isFailed, setIsFailed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentCount, setAgentCount] = useState(0);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;
  const doneRef = useRef(false);

  const handleComplete = useCallback(async () => {
    try {
      const evaluation = await evaluationApi.get(submissionId);
      onCompleteRef.current(evaluation);
    } catch {
      setError('Failed to fetch evaluation results');
    }
  }, [submissionId]);

  useEffect(() => {
    if (!submissionId) return;

    const token =
      typeof window !== 'undefined'
        ? localStorage.getItem('access_token')
        : null;
    const url = evaluationApi.getStreamUrl(submissionId);
    const eventSource = new EventSource(
      `${url}?token=${encodeURIComponent(token || '')}`
    );

    eventSource.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string);
        const status: EvaluationStage = data.status ?? 'pending';
        const msg: string | undefined = data.message;
        const count: number = data.agent_count ?? 0;

        setCurrentStage(status);
        setAgentCount(count);
        setStages(buildStages(status, msg));
        setProgress(
          data.progress != null
            ? (data.progress as number)
            : (STAGE_PROGRESS[status] ?? 0)
        );

        if (status === 'completed') {
          doneRef.current = true;
          setIsComplete(true);
          eventSource.close();
          handleComplete();
        } else if (status === 'failed') {
          doneRef.current = true;
          setIsFailed(true);
          setError(msg ?? 'Evaluation failed');
          eventSource.close();
        }
      } catch {
        // ignore parse errors
      }
    };

    eventSource.onerror = () => {
      if (!doneRef.current) {
        setError('Connection lost. Evaluation may still be running.');
        eventSource.close();
      }
    };

    return () => {
      eventSource.close();
    };
  }, [submissionId, handleComplete]);

  return { stages, currentStage, progress, isComplete, isFailed, error, agentCount };
}
