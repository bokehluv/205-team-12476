import QtQuick 2.0

Item {
    id: root
    property var divColor: "white"
    property var bgColor: "transparent"
    property var leftSource: "http://images.clipartpanda.com/rocket-clipart-nicubunu_Toy_rocket.png"
    property var rightSource: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/SNice.svg/1200px-SNice.svg.png"

    // When the size of the item is changed, we want to keep the divider at the same
    // relative position. If the relative position is undefined, we default to 0.5
    onWidthChanged: {
        div.x = div.relX ? width*div.relX : width*0.5
    }

    // Allows you to click anywhere on the pictures to move the divider
    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: div.x = mouseX
    }

    // Right image. It is at the bottom, and fills the entire item
    Rectangle {
        anchors.fill: parent
        color: bgColor

        Image {
            source: rightSource
            anchors.fill: parent
        }
    }

    // Left image. It is overlayed on the right image, and fills from the left to the divider
    Rectangle {
        anchors {
            left: parent.left
            right: div.left
            top: parent.top
            bottom: parent.bottom
        }
        color: bgColor
        clip: true
        // The actual image is actually just as large as the containing item
        Image {
            width: root.width
            height: root.height
            source: leftSource
        }
    }

    // The divider
    Rectangle {
        id: div
        property double relX: x/root.width
        x: root.width/2
        width: 5
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        color: divColor
        border.color: "black"
        border.width: 1

        MouseArea {
            id: dragArea
            anchors {
                top: parent.top
                bottom: parent.bottom
                right: rightArrow.right
                left: leftArrow.left
            }

            drag.target: parent
            cursorShape: Qt.SizeHorCursor
            hoverEnabled: true
        }

        Drag.active: dragArea.drag.active
        // Keep divider from going outside the limits
        onXChanged: {
            if (x > parent.width - width) x = parent.width - width
            if (x < 0) x = 0
        }

        // Right arrow
        Canvas {
            id: rightArrow
            anchors {
                left: parent.right
                verticalCenter: parent.verticalCenter
                leftMargin: dragArea.containsMouse ? 5 : 2
            }
            width: 20
            height: 20
            opacity: 0.5
            onPaint: {
                var ctx = getContext("2d");
                ctx.fillStyle = divColor;
                ctx.strokeStyle = "black";
                ctx.beginPath();
                ctx.moveTo(0,0);
                ctx.lineTo(width,height/2);
                ctx.lineTo(0,height);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }
            Behavior on anchors.leftMargin { PropertyAnimation{ duration: 150} }
        }

        // Left arrow
        Canvas {
            id: leftArrow
            anchors {
                right: parent.left
                verticalCenter: parent.verticalCenter
                rightMargin: dragArea.containsMouse ? 5 : 2
            }
            width: 20
            height: 20
            opacity: 0.5
            onPaint: {
                var ctx = getContext("2d");
                ctx.fillStyle = divColor
                ctx.strokeStyle = "black";
                ctx.beginPath();
                ctx.moveTo(width,0);
                ctx.lineTo(0,height/2);
                ctx.lineTo(width,height);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }
            Behavior on anchors.rightMargin { PropertyAnimation{ duration: 150} }
        }
    }

}
