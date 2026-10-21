import Foundation

/// Platform independent sRGB channels; preserves alpha in both generated outputs.
public struct DesignColor: Equatable, Sendable {
  public let red: Double
  public let green: Double
  public let blue: Double
  public let alpha: Double

  public init(red: Double, green: Double, blue: Double, alpha: Double = 1) {
    self.red = red
    self.green = green
    self.blue = blue
    self.alpha = alpha
  }
}

#if canImport(SwiftUI)
  import SwiftUI

  extension DesignColor {
    public var color: Color {
      Color(.sRGB, red: red, green: green, blue: blue, opacity: alpha)
    }
  }
#endif
