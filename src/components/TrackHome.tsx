import {
  Avatar,
  Badge,
  Button,
  Column,
  Heading,
  RevealFx,
  Row,
  Schema,
  Text,
} from "@once-ui-system/core";
import { about, baseURL, person, tracks } from "@/resources";
import { Projects } from "@/components/work/Projects";
import { TrackSwitcher } from "@/components/TrackSwitcher";

/**
 * Shared layout for the two track landing pages (/finance and /research).
 * Everything that differs between them lives in `tracks` in content.tsx.
 */
export function TrackHome({ track }: { track: "finance" | "research" }) {
  const t = tracks[track];

  return (
    <Column maxWidth="m" gap="xl" paddingY="12" horizontal="center">
      <Schema
        as="webPage"
        baseURL={baseURL}
        path={t.path}
        title={t.title}
        description={t.description}
        image={`/api/og/generate?title=${encodeURIComponent(t.title)}`}
        author={{
          name: person.name,
          url: `${baseURL}${about.path}`,
          image: `${baseURL}${person.avatar}`,
        }}
      />
      <Column fillWidth horizontal="center" gap="m">
        <RevealFx fillWidth horizontal="center" paddingTop="8" paddingBottom="24">
          <TrackSwitcher active={track} />
        </RevealFx>
        <Column maxWidth="s" horizontal="center" align="center">
          {t.featured.display && (
            <RevealFx
              fillWidth
              horizontal="center"
              paddingTop="8"
              paddingBottom="32"
              paddingLeft="12"
            >
              <Badge
                background="brand-alpha-weak"
                paddingX="12"
                paddingY="4"
                onBackground="neutral-strong"
                textVariant="label-default-s"
                arrow={false}
                href={t.featured.href}
              >
                <Row paddingY="2">{t.featured.title}</Row>
              </Badge>
            </RevealFx>
          )}
          <RevealFx translateY="4" fillWidth horizontal="center" paddingBottom="16">
            <Heading wrap="balance" variant="display-strong-l">
              {t.headline}
            </Heading>
          </RevealFx>
          <RevealFx translateY="8" delay={0.2} fillWidth horizontal="center" paddingBottom="32">
            <Text wrap="balance" onBackground="neutral-weak" variant="heading-default-xl">
              {t.subline}
            </Text>
          </RevealFx>
          <RevealFx paddingTop="12" delay={0.4} horizontal="center" paddingLeft="12">
            <Button
              id="about"
              data-border="rounded"
              href={about.path}
              variant="secondary"
              size="m"
              weight="default"
              arrowIcon
            >
              <Row gap="8" vertical="center" paddingRight="4">
                {about.avatar.display && (
                  <Avatar
                    marginRight="8"
                    style={{ marginLeft: "-0.75rem" }}
                    src={person.avatar}
                    size="m"
                  />
                )}
                {about.title}
              </Row>
            </Button>
          </RevealFx>
        </Column>
      </Column>
      <RevealFx translateY="16" delay={0.6}>
        <Projects track={track} range={[1, 1]} />
      </RevealFx>
      <Projects track={track} range={[2]} />
    </Column>
  );
}
