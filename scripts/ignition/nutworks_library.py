# NutWorks MES - Ignition Script Library
# Paste this into Designer > Scripting > Project Library > nutworks

def createWorkOrder(productName, nutMixType, targetQty):
    woId = "WO-" + system.date.format(system.date.now(), "yyyyMMdd-HHmm")
    query = """INSERT INTO work_orders
            (work_order_id, product_name, nut_mix_type, target_qty_kg)
            VALUES (?, ?, ?, ?)"""
    system.db.runPrepUpdate(query,
                            [woId, productName, nutMixType, targetQty],
                            "nutworks_db")
    system.tag.writeBlocking(["[default]NutWorks/Production/WorkOrder_ID"], [woId])
    system.tag.writeBlocking(["[default]NutWorks/Production/Target_Qty_kg"], [targetQty])
    return woId


def receiveLot(materialType, qtyKg, siloNumber):
    lotNumber = "LOT-" + system.date.format(system.date.now(), "yyyyMMddHHmmss")
    system.db.runPrepUpdate(
        """INSERT INTO material_lots
        (lot_number, material_type, received_qty_kg, silo_location)
        VALUES (?, ?, ?, ?)""",
        [lotNumber, materialType, qtyKg, "Silo" + str(siloNumber)],
        "nutworks_db")
    tagPath = "[default]NutWorks/Receiving/Silo" + str(siloNumber) + "_Weight_kg"
    current = system.tag.readBlocking([tagPath])[0].value
    system.tag.writeBlocking([tagPath], [current + qtyKg])
    return lotNumber


def calculateOEE(shiftDate, shift):
    plannedMinutes = 720
    downtimeQuery = """SELECT COALESCE(SUM(value), 0) FROM production_log
                    WHERE event_type = 'DOWNTIME'
                    AND DATE(timestamp) = ?"""
    downtime = system.db.runScalarQuery(downtimeQuery, [shiftDate], "nutworks_db")
    availability = ((plannedMinutes - downtime) / plannedMinutes) * 100
    actualRate = system.tag.readBlocking(
                ["[default]NutWorks/Roasting/Roaster_Output_kg_hr"])[0].value
    idealRate = 500
    performance = min((actualRate / idealRate) * 100, 100)
    produced = system.tag.readBlocking(
            ["[default]NutWorks/Production/Produced_Qty_kg"])[0].value
    target = system.tag.readBlocking(
            ["[default]NutWorks/Production/Target_Qty_kg"])[0].value
    quality = min((produced / target) * 100, 100) if target > 0 else 0
    oee = (availability * performance * quality) / 10000
    system.tag.writeBlocking(["[default]NutWorks/Production/Shift_OEE_pct"], [oee])
    system.db.runPrepUpdate(
        """INSERT INTO oee_log
        (shift_date, shift, availability_pct, performance_pct,
            quality_pct, oee_pct)
        VALUES (?, ?, ?, ?, ?, ?)""",
        [shiftDate, shift, availability, performance, quality, oee],
        "nutworks_db")
    return {"availability": availability, "performance": performance,
            "quality": quality, "oee": oee}


def logEvent(workOrderId, station, eventType, value, unit, notes=""):
    system.db.runPrepUpdate(
        """INSERT INTO production_log
        (work_order_id, station, event_type, value, unit, notes)
        VALUES (?, ?, ?, ?, ?, ?)""",
        [workOrderId, station, eventType, value, unit, notes],
        "nutworks_db")