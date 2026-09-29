import { getPosts } from "@/utils/utils";
import { Column, Heading, Media, Row, SmartLink, Text } from "@once-ui-system/core";

interface WorkGridProps {
  track?: string;
  title?: string;
  columns?: string;
}

/**
 * Compact card grid for a track's work, in place of full-width image cards.
 * Each card leads with its tag so the breadth of a track is readable at a
 * glance rather than after four screens of scrolling.
 */
export function WorkGrid({ track, title = "Selected work", columns = "2" }: WorkGridProps) {
  let projects = getPosts(["src", "app", "work", "projects"]);

  if (track) {
    projects = projects.filter((post) => post.metadata.track === track);
  }

  projects.sort(
    (a, b) =>
      new Date(b.metadata.publishedAt).getTime() - new Date(a.metadata.publishedAt).getTime(),
  );

  return (
    <Column fillWidth gap="24" paddingX="l" marginBottom="40">
      <Heading as="h2" variant="display-strong-xs" wrap="balance">
        {title}
      </Heading>
      <Row fillWidth gap="16" wrap s={{ direction: "column" }}>
        {projects.map((post) => (
          <SmartLink
            key={post.slug}
            href={`/work/${post.slug}`}
            unstyled
            style={{ flex: `1 1 calc(${100 / Number(columns)}% - 1rem)`, minWidth: "17rem" }}
          >
            <Column
              fillWidth
              fillHeight
              gap="8"
              padding="12"
              radius="m"
              border="neutral-alpha-weak"
              background="surface"
            >
              {post.metadata.images?.[0] && (
                <Media
                  src={post.metadata.images[0]}
                  alt={post.metadata.title}
                  aspectRatio="16 / 9"
                  radius="s"
                  sizes="(max-width: 960px) 100vw, 480px"
                  marginBottom="8"
                />
              )}
              <Column gap="8" paddingX="8" paddingBottom="8">
              {post.metadata.tag && (
                <Row gap="8" vertical="center">
                  <Row
                    width="8"
                    height="8"
                    radius="full"
                    background="brand-strong"
                    style={{ flexShrink: 0 }}
                  />
                  <Text variant="label-default-s" onBackground="brand-medium">
                    {post.metadata.tag}
                  </Text>
                </Row>
              )}
              <Text variant="heading-strong-s" onBackground="neutral-strong" wrap="balance">
                {post.metadata.title}
              </Text>
              <Text variant="body-default-s" onBackground="neutral-weak" wrap="balance">
                {post.metadata.summary}
              </Text>
              </Column>
            </Column>
          </SmartLink>
        ))}
      </Row>
    </Column>
  );
}
