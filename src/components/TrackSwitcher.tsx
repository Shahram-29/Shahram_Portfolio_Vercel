"use client";

import { Row, ToggleButton } from "@once-ui-system/core";
import { tracks } from "@/resources";

/**
 * Segmented switch between the two sides of the portfolio.
 * `active` is the track key of the page currently being rendered.
 */
export const TrackSwitcher = ({ active }: { active: "finance" | "research" }) => {
  return (
    <Row
      background="page"
      border="neutral-alpha-weak"
      radius="m-4"
      shadow="l"
      padding="4"
      gap="4"
      horizontal="center"
      data-border="rounded"
    >
      <ToggleButton
        prefixIcon="grid"
        href={tracks.finance.path}
        label={tracks.finance.label}
        selected={active === "finance"}
      />
      <ToggleButton
        prefixIcon="book"
        href={tracks.research.path}
        label={tracks.research.label}
        selected={active === "research"}
      />
    </Row>
  );
};
