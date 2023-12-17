package com.google.mediapipe.apps.posetrackinggpu;

import android.os.Bundle;
import android.util.Log;
import com.google.mediapipe.formats.proto.LandmarkProto.NormalizedLandmark;
import com.google.mediapipe.formats.proto.LandmarkProto.NormalizedLandmarkList;
import com.google.mediapipe.framework.PacketGetter;
import com.google.protobuf.InvalidProtocolBufferException;

import java.util.Scanner;
import android.widget.TextView;

/** Main activity of MediaPipe pose tracking app. */
public class MainActivity extends com.google.mediapipe.apps.basic.MainActivity {
    private static final String TAG = "MainActivity";

    private static final String OUTPUT_LANDMARKS_STREAM_NAME = "pose_landmarks";

    private NormalizedLandmark leftShoulderRef;
    private NormalizedLandmark rightShoulderRef;

    private long jumpStartTime = -1; // Timestamp when the jump starts
    private long jumpEndTime = -1;   // Timestamp when the jump ends
    private float maxJumpHeight = 0; // Maximum jump height observed
    private float maxJumpDuration = 0; // Maximum jump duration observed

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // To show verbose logging, run:
        // adb shell setprop log.tag.MainActivity VERBOSE


        // Input tinggi badan
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter your height in centimeters: ");
        float tinggiBadan = scanner.nextFloat();

        // Get user input for camera or video file
        Scanner scanner = new Scanner(System.in);
        System.out.print("Press 'c' to open the camera or 'v' to choose a video file: ");
        String userInput = scanner.nextLine().toLowerCase();

        if (userInput.equals("c")) {
            // Open the camera
            openCamera();
        } else if (userInput.equals("v")) {
            // Choose a video file
            chooseVideoFile();
        } else {
            Log.e(TAG, "Invalid input. Exiting.");
            finish();
        }
    }

    private void openCamera() {
        if (Log.isLoggable(TAG, Log.VERBOSE)) {
            processor.addPacketCallback(
                    OUTPUT_LANDMARKS_STREAM_NAME,
                    (packet) -> {
                        Log.v(TAG, "Received pose landmarks packet.");
                        try {
                            NormalizedLandmarkList poseLandmarks =
                                    PacketGetter.getProto(packet, NormalizedLandmarkList.class);

                            // Calculate jump height and duration based on shoulders
                            processJump(poseLandmarks, packet.getTimestamp());

                        } catch (InvalidProtocolBufferException exception) {
                            Log.e(TAG, "Failed to get proto.", exception);
                        }
                    });
        }
    }

    private void chooseVideoFile() {
        // Implement the logic to choose a video file from local storage
        // and replace the following line with your actual implementation.
        Log.d(TAG, "Choosing video file from local storage. Replace this line with your code.");
    }

    private float calculateScale(NormalizedLandmarkList poseLandmarks) {
        NormalizedLandmark nose = poseLandmarks.getLandmark(LandmarkType.NOSE.getIndex());
        NormalizedLandmark rightAnkle = poseLandmarks.getLandmark(LandmarkType.RIGHT_ANKLE.getIndex());
        NormalizedLandmark leftAnkle = poseLandmarks.getLandmark(LandmarkType.LEFT_ANKLE.getIndex());

        float noseY = nose.getY() * 1280; // Assuming 1280 is the height of the frame in pixels
        float rightAnkleY = rightAnkle.getY() * 1280;
        float leftAnkleY = leftAnkle.getY() * 1280;

        float jarakHeelX = Math.abs(rightAnkle.getX() - leftAnkle.getX()) * 1280; // Assuming 1280 is width of the frame
        float jarakHeelY = Math.abs(rightAnkleY - leftAnkleY);
        float jarakHeel = (float) (Math.sqrt(Math.pow(jarakHeelX, 2) + Math.pow(jarakHeelY, 2))) / 2;

        float averageAnkleY = (rightAnkleY + leftAnkleY) / 2;
        float hypotenusa = Math.abs(averageAnkleY - noseY);
        float heightPixel = (float) Math.sqrt(Math.pow(hypotenusa, 2) - Math.pow(jarakHeel, 2));

        return (tinggiBadan / heightPixel) / 2.53f;
    }

    private float SCALE = -1.0f; // Initialize SCALE to a sentinel value

    private void processJump(NormalizedLandmarkList poseLandmarks, long timestamp) {
        // Assume LEFT_SHOULDER and RIGHT_SHOULDER are the landmarks corresponding to the shoulders
        NormalizedLandmark leftShoulder = poseLandmarks.getLandmark(Shoulder.LEFT_SHOULDER.getNumber());
        NormalizedLandmark rightShoulder = poseLandmarks.getLandmark(Shoulder.RIGHT_SHOULDER.getNumber());
    
        // Calculate the scale once when landmarks are first detected
        if (SCALE == -1.0f) {
            SCALE = calculateScale(poseLandmarks);
        }

        if (leftShoulderRef == null || rightShoulderRef == null) {
            // Capture the reference positions during the first detection
            leftShoulderRef = leftShoulder;
            rightShoulderRef = rightShoulder;
        }

        // Calculate the reference line
        float refLineStartX = leftShoulderRef.getX();
        float refLineStartY = leftShoulderRef.getY();
        float refLineEndX = rightShoulderRef.getX();
        float refLineEndY = rightShoulderRef.getY();

        // Draw the reference line (you may need to adapt this based on your visualization logic)
        drawLine(refLineStartX, refLineStartY, refLineEndX, refLineEndY);

        // Calculate the dynamic line based on the current user position
        float dynamicLineStartX = leftShoulder.getX();
        float dynamicLineStartY = leftShoulder.getY();
        float dynamicLineEndX = rightShoulder.getX();
        float dynamicLineEndY = rightShoulder.getY();

        // Draw the dynamic line (you may need to adapt this based on your visualization logic)
        drawLine(dynamicLineStartX, dynamicLineStartY, dynamicLineEndX, dynamicLineEndY);

        // Calculate jump height and duration based on the dynamic line (convert to cm)
        float jumpHeight = Math.abs(dynamicLineStartY - dynamicLineEndY) * SCALE;

        // Check if the person is in the air (jumping)
        if (isInAir(poseLandmarks, 0)) {
            // Update jump start time if it's the first frame of the jump
            if (jumpStartTime == -1) {
                jumpStartTime = timestamp;
            }
            // Update max jump height
            if (jumpHeight > maxJumpHeight) {
                maxJumpHeight = jumpHeight;
            }
        } else {
            // Check if the person has landed (end of jump)
            if (jumpStartTime != -1) {
                jumpEndTime = timestamp;
                long jumpDuration = jumpEndTime - jumpStartTime;
                // Update max jump duration
                if (jumpDuration > maxJumpDuration) {
                    maxJumpDuration = jumpDuration;
                }
                // Reset jump start time for the next jump
                jumpStartTime = -1;
            }
        }

        // Log or use the jumpHeight and maxJumpDuration as needed
        Log.v(TAG, "Jump Height: " + jumpHeight + "cm");
        Log.v(TAG, "Max Jump Duration: " + maxJumpDuration + "seconds");

        //tambahin xml
    }

    private void drawLine(float startX, float startY, float endX, float endY) {
        // Implement your logic to draw a line based on the provided coordinates
        // This could be visualized on an image or in your UI.
        Log.d(TAG, "Drawing line from (" + startX + ", " + startY + ") to (" + endX + ", " + endY + ")");
    }

    private boolean isInAir(NormalizedLandmarkList poseLandmarks, long frameNumberOrTimestamp) {
        NormalizedLandmark leftFoot = poseLandmarks.getLandmark(LandmarkType.LEFT_FOOT_INDEX.getNumber());
        NormalizedLandmark rightFoot = poseLandmarks.getLandmark(LandmarkType.RIGHT_FOOT_INDEX.getNumber());

        if (referenceLeftFoot == null || referenceRightFoot == null) {
        referenceLeftFoot = leftFoot;
        referenceRightFoot = rightFoot;
        } else {
        // Check if both feet are off the ground
            if (leftFoot.getY() < referenceLeftFoot.getY() && rightFoot.getY() < referenceRightFoot.getY() && jumpStartFrame == null) {
            jumpStartFrame = frameNumberOrTimestamp; // Get the current frame number or timestamp
            }

        // Check if feet have returned to the ground
            if (jumpStartFrame != null && leftFoot.getY() >= referenceLeftFoot.getY() && rightFoot.getY() >= referenceRightFoot.getY()) {
            jumpEndFrame = frameNumberOrTimestamp; // Get the current frame number or timestamp
            long jumpDuration = jumpEndFrame - jumpStartFrame; // Calculate jump duration
            jumpStartFrame = null; // Reset jump start frame for the next jump
            // You can store jumpDuration or use it as needed
            }
        }

    // Determine if in the air
        return leftFoot.getY() < referenceLeftFoot.getY() && rightFoot.getY() < referenceRightFoot.getY();
    }   

}