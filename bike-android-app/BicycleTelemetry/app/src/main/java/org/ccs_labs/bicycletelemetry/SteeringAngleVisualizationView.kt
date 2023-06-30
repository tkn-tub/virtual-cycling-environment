package org.ccs_labs.bicycletelemetry

import android.content.Context
import android.graphics.Canvas
import android.graphics.drawable.Drawable
import androidx.vectordrawable.graphics.drawable.VectorDrawableCompat
import android.util.AttributeSet
import android.view.View

/**
 * This class is not yet used!
 * TODO: document your custom view class.
 */
class SteeringAngleVisualizationView : View {

//    private var _exampleString: String? = null // TODO: use a default from R.string...
//    private var _exampleColor: Int = Color.RED // TODO: use a default from R.color...
//    private var _exampleDimension: Float = 0f // TODO: use a default from R.dimen...
//
//    private var textPaint: TextPaint? = null
//    private var textWidth: Float = 0f
//    private var textHeight: Float = 0f

    private var _currentAzimuth: Float = 0f

    private var mBikeFrame: Drawable? = null
    private var mBikeHandle: Drawable? = null
    private var mBikeFrontWheel: Drawable? = null

    /**
     * The current steering angle / azimuth to visualize
     */
    var currentAzimuth: Float
        get() = _currentAzimuth
        set(value) {
            _currentAzimuth = value
            //invalidateTextPaintAndMeasurements() // TODO: invalidate drawing
        }

//    /**
//     * The font color
//     */
//    var exampleColor: Int
//        get() = _exampleColor
//        set(value) {
//            _exampleColor = value
//            invalidateTextPaintAndMeasurements()
//        }
//
//    /**
//     * In the example view, this dimension is the font size.
//     */
//    var exampleDimension: Float
//        get() = _exampleDimension
//        set(value) {
//            _exampleDimension = value
//            invalidateTextPaintAndMeasurements()
//        }
//
//    /**
//     * In the example view, this drawable is drawn above the text.
//     */
//    var exampleDrawable: Drawable? = null

    constructor(context: Context) : super(context) {
        init(null, 0)
    }

    constructor(context: Context, attrs: AttributeSet) : super(context, attrs) {
        init(attrs, 0)
    }

    constructor(context: Context, attrs: AttributeSet, defStyle: Int) : super(context, attrs, defStyle) {
        init(attrs, defStyle)
    }

    private fun init(attrs: AttributeSet?, defStyle: Int) {
        // Load attributes
        val a = context.obtainStyledAttributes(
            attrs, R.styleable.SteeringAngleVisualizationView, defStyle, 0
        )

        val bikeFrameResourceId = a.getResourceId(R.styleable.SteeringAngleVisualizationView_bikeFrameSrc,
            R.drawable.vec_bike_frame)
        mBikeFrame = VectorDrawableCompat.create(resources, bikeFrameResourceId, null)

        val bikeHandleResourceId = a.getResourceId(R.styleable.SteeringAngleVisualizationView_bikeFrameSrc,
            R.drawable.vec_bike_frame)
        mBikeHandle = VectorDrawableCompat.create(resources, bikeHandleResourceId, null)

        val bikeFrontWheelResourceId = a.getResourceId(R.styleable.SteeringAngleVisualizationView_bikeFrameSrc,
            R.drawable.vec_bike_frame)
        mBikeFrontWheel = VectorDrawableCompat.create(resources, bikeFrontWheelResourceId, null)

//        _exampleString = a.getString(
//            R.styleable.SteeringAngleVisualizationView_exampleString
//        )
//        _exampleColor = a.getColor(
//            R.styleable.SteeringAngleVisualizationView_exampleColor,
//            exampleColor
//        )
//        // Use getDimensionPixelSize or getDimensionPixelOffset when dealing with
//        // values that should fall on pixel boundaries.
//        _exampleDimension = a.getDimension(
//            R.styleable.SteeringAngleVisualizationView_exampleDimension,
//            exampleDimension
//        )
//
//        if (a.hasValue(R.styleable.SteeringAngleVisualizationView_exampleDrawable)) {
//            exampleDrawable = a.getDrawable(
//                R.styleable.SteeringAngleVisualizationView_exampleDrawable
//            )
//            exampleDrawable?.callback = this
//        }

        a.recycle()

        // Set up a default TextPaint object
//        textPaint = TextPaint().apply {
//            flags = Paint.ANTI_ALIAS_FLAG
//            textAlign = Paint.Align.LEFT
//        }
//
//        // Update TextPaint and text measurements from attributes
//        invalidateTextPaintAndMeasurements()
    }

//    private fun invalidateTextPaintAndMeasurements() {
//        textPaint?.let {
//            it.textSize = exampleDimension
//            it.color = exampleColor
//            textWidth = it.measureText(exampleString)
//            textHeight = it.fontMetrics.bottom
//        }
//    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

//        // TODO: consider storing these as member variables to reduce
//        // allocations per draw cycle.
//        val paddingLeft = paddingLeft
//        val paddingTop = paddingTop
//        val paddingRight = paddingRight
//        val paddingBottom = paddingBottom
//
//        val contentWidth = width - paddingLeft - paddingRight
//        val contentHeight = height - paddingTop - paddingBottom

        // TODO: draw bike handle at current rotation, maybe plot angles over time

//        exampleString?.let {
//            // Draw the text.
//            canvas.drawText(
//                it,
//                paddingLeft + (contentWidth - textWidth) / 2,
//                paddingTop + (contentHeight + textHeight) / 2,
//                textPaint
//            )
//        }
//
//        // Draw the example drawable on top of the text.
//        exampleDrawable?.let {
//            it.setBounds(
//                paddingLeft, paddingTop,
//                paddingLeft + contentWidth, paddingTop + contentHeight
//            )
//            it.draw(canvas)
//        }
    }
}
