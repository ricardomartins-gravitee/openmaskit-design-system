#if canImport(SwiftUI)
  import SwiftUI

  /// Semantic typography uses native system fonts on macOS.
  public enum OpenMaskitTypography {
    public static var body: Font { .system(size: OpenMaskitTokens.fontSizeBody) }
    public static var caption: Font { .system(size: OpenMaskitTokens.fontSizeCaption) }
    public static var title: Font {
      .system(size: OpenMaskitTokens.fontSizeTitle, weight: .semibold, design: .monospaced)
    }
    public static var section: Font {
      .system(size: OpenMaskitTokens.fontSizeSection, weight: .semibold, design: .monospaced)
    }
  }

  public struct OpenMaskitPanel<Content: View>: View {
    let title: String
    let detail: String?
    let content: Content

    public init(_ title: String, detail: String? = nil, @ViewBuilder content: () -> Content) {
      self.title = title
      self.detail = detail
      self.content = content()
    }

    public var body: some View {
      VStack(alignment: .leading, spacing: OpenMaskitTokens.componentPanelGap) {
        HStack(spacing: OpenMaskitTokens.spaceSm) {
          RoundedRectangle(cornerRadius: 1).fill(OpenMaskitTheme.accent)
            .frame(width: 3, height: OpenMaskitTokens.fontSizeSection)
          Text(title).font(OpenMaskitTypography.section).accessibilityAddTraits(.isHeader)
          Spacer()
          if let detail {
            Text(detail).font(OpenMaskitTypography.caption).foregroundStyle(
              OpenMaskitTheme.secondary)
          }
        }
        content
      }
      .padding(OpenMaskitTokens.componentPanelPadding)
      .frame(maxWidth: .infinity, alignment: .leading)
      .background(
        OpenMaskitTheme.surface,
        in: RoundedRectangle(cornerRadius: OpenMaskitTokens.componentPanelRadius)
      )
      .overlay(
        RoundedRectangle(cornerRadius: OpenMaskitTokens.componentPanelRadius)
          .stroke(OpenMaskitTheme.border, lineWidth: 1))
    }
  }

  public struct OpenMaskitBadge: View {
    let title: String
    let color: Color

    public init(title: String, color: Color) {
      self.title = title
      self.color = color
    }

    public var body: some View {
      Text(title)
        .font(.system(size: OpenMaskitTokens.fontSizeBadge, weight: .medium, design: .monospaced))
        .foregroundStyle(color)
        .padding(.horizontal, OpenMaskitTokens.componentBadgePaddingX)
        .padding(.vertical, OpenMaskitTokens.componentBadgePaddingY)
        .background(
          color.opacity(OpenMaskitTokens.opacityBadgeFill),
          in: RoundedRectangle(cornerRadius: OpenMaskitTokens.componentBadgeRadius)
        )
        .overlay(
          RoundedRectangle(cornerRadius: OpenMaskitTokens.componentBadgeRadius)
            .stroke(color.opacity(OpenMaskitTokens.opacityBadgeBorder), lineWidth: 1))
    }
  }

  public struct OpenMaskitButtonStyle: ButtonStyle {
    public enum Kind { case primary, secondary, danger }
    let kind: Kind
    @Environment(\.isEnabled) private var isEnabled

    public init(kind: Kind = .secondary) { self.kind = kind }

    public func makeBody(configuration: Configuration) -> some View {
      let tint = kind == .danger ? OpenMaskitTheme.red : OpenMaskitTheme.accent
      return configuration.label
        .font(.system(size: OpenMaskitTokens.componentButtonFontSize, weight: .medium))
        .foregroundStyle(kind == .primary ? OpenMaskitTheme.root : tint)
        .padding(.horizontal, OpenMaskitTokens.componentButtonPaddingX)
        .padding(.vertical, OpenMaskitTokens.componentButtonPaddingY)
        .background(
          kind == .primary ? tint : OpenMaskitTheme.elevated,
          in: RoundedRectangle(cornerRadius: OpenMaskitTokens.componentButtonRadius)
        )
        .overlay(
          RoundedRectangle(cornerRadius: OpenMaskitTokens.componentButtonRadius)
            .stroke(kind == .primary ? Color.clear : tint.opacity(0.30), lineWidth: 1)
        )
        .opacity(
          isEnabled
            ? (configuration.isPressed ? OpenMaskitTokens.opacityPressed : 1)
            : OpenMaskitTokens.opacityDisabled)
    }
  }
#endif
