"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { API_BASE_URL, api } from "@/lib/api/client";

export type LiveEvent = {
  event_type:
    | "district_conditions_changed"
    | "incident_action_updated"
    | "report_submitted"
    | "shield_changed";
  district_id: string;
  resource_id: string | null;
  summary: string;
  occurred_at: string;
};

export type ConnectionState = "connecting" | "live" | "offline";

const FIRST_RETRY_MS = 1_000;
const MAX_RETRY_MS = 15_000;

function socketUrl(ticket: string): string {
  const base = new URL(API_BASE_URL);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = "/ws";
  base.searchParams.set("ticket", ticket);
  return base.toString();
}

function affectedKeys(event: LiveEvent): string[][] {
  const district = event.district_id;
  switch (event.event_type) {
    case "district_conditions_changed":
      return [
        ["districts"],
        ["alerts"],
        ["district", district],
        ["forecast", district],
        ["readiness", district],
      ];
    case "incident_action_updated":
      return [["incident", district]];
    case "report_submitted":
      return [["reports", district], ["reports"], ["readiness", district]];
    case "shield_changed":
      return [["shield", district]];
  }
}

export function useLiveEvents(token: string | null) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<ConnectionState>("connecting");
  const [lastEvent, setLastEvent] = useState<LiveEvent | null>(null);
  const retryDelay = useRef(FIRST_RETRY_MS);
  const socket = useRef<WebSocket | null>(null);
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const closedByUs = useRef(false);

  const handle = useCallback(
    (event: LiveEvent) => {
      setLastEvent(event);
      for (const key of affectedKeys(event)) {
        void queryClient.invalidateQueries({ queryKey: key });
      }
    },
    [queryClient],
  );

  useEffect(() => {
    if (!token) return;

    closedByUs.current = false;

    // A ticket is fetched for every attempt, including reconnections: it is
    // single-use by design, so a retry with the previous one would be refused.
    const connect = async () => {
      setState("connecting");
      let ticket: string;
      try {
        ticket = (await api.streamTicket(token)).ticket;
      } catch {
        if (closedByUs.current) return;
        setState("offline");
        retryTimer.current = setTimeout(
          () => void connect(),
          retryDelay.current,
        );
        retryDelay.current = Math.min(retryDelay.current * 2, MAX_RETRY_MS);
        return;
      }
      if (closedByUs.current) return;

      const next = new WebSocket(socketUrl(ticket));
      socket.current = next;

      next.onopen = () => {
        retryDelay.current = FIRST_RETRY_MS;
        setState("live");
      };

      next.onmessage = (message) => {
        try {
          handle(JSON.parse(message.data as string) as LiveEvent);
        } catch {
          // A malformed frame is not worth tearing the connection down for.
        }
      };

      next.onclose = () => {
        if (closedByUs.current) return;
        setState("offline");
        retryTimer.current = setTimeout(
          () => void connect(),
          retryDelay.current,
        );
        retryDelay.current = Math.min(retryDelay.current * 2, MAX_RETRY_MS);
      };

      next.onerror = () => next.close();
    };

    void connect();

    return () => {
      closedByUs.current = true;
      if (retryTimer.current) clearTimeout(retryTimer.current);
      socket.current?.close();
    };
  }, [token, handle]);

  return { state, lastEvent };
}
