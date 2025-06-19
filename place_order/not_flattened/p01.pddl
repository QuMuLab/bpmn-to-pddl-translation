(define (problem p01-bpmn-no-flatten)
        (:domain place_order_no_flatten)
        (:objects
    Activity_08v385w Activity_0fclwek Activity_0hpwxsm Activity_1vopca8 Activity_1wqi2kf Activity_1x6npxm - task
    Event_12xfkhi StartEvent_1 - event
    Gateway_04hl5tz Gateway_1la9igl Gateway_1nuiirw Gateway_1yg27bh - gateway
        )
        (:init (StartEvent_1))
        (:goal (and (done)))
        )
    