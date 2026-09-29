import { Column, Heading, Row, Text } from "@once-ui-system/core";

type Stat = { value: string; label: string };

/**
 * The figures strip under the hero. Four numbers, each one checkable against
 * something on the site — no vanity metrics.
 */
export function TrackStats({ stats }: { stats: readonly Stat[] }) {
  return (
    <Row
      fillWidth
      gap="24"
      paddingX="l"
      paddingY="24"
      s={{ direction: "column" }}
      horizontal="center"
    >
      {stats.map((stat) => (
        <Column key={stat.label} flex={1} gap="4">
          <Heading variant="display-strong-xs" onBackground="neutral-strong">
            {stat.value}
          </Heading>
          <Text variant="body-default-s" onBackground="neutral-weak" wrap="balance">
            {stat.label}
          </Text>
        </Column>
      ))}
    </Row>
  );
}
